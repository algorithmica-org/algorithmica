---
title: Search Trees
weight: 3
draft: true
---

In the [previous article](../s-tree), we designed and implemented *static* B-trees to speed up binary searching in sorted arrays, and in its [last section](../s-tree/#as-a-dynamic-tree), we briefly discussed how to make them *dynamic* back while retaining the performance gains from [SIMD](/hpc/simd), and validated our predictions by adding and following explicit pointers in the internal nodes of the S+ tree.

In this article, we follow up on that proposition and design a minimally functional search tree for integer keys, [achieving](#evaluation) up to 18x/8x speedup over `std::set` and up to 7x/2x speedup over [`absl::btree`](https://abseil.io/blog/20190812-btree) for `lower_bound` and `insert` queries respectively, with yet ample room for improvement.

The memory overhead of the structure is around 30%, and the [final implementation](https://github.com/sslotin/amh-code/blob/main/b-tree/btree-final.cc) is under 150 lines of C.

<!--

7-18x/3-8x speedup over `std::set` and 3-7x/1.5-2x

that we call *B− tree*

-->

## B− Tree

Instead of making small incremental improvements like we usually do in other case studies, in this article, we will implement just one data structure that we name *B− tree*, which is based on the [B+ tree](../s-tree/#b-tree-layout-1), with a few minor differences:

- Nodes in the B− tree do not store any pointers or meta-information whatsoever except for the pointers to internal node children (while the B+ tree leaf nodes store a pointer to the next leaf node). This lets us perfectly place the keys in the leaf nodes on cache lines.
- We define key $i$ to be the *maximum* key in the subtree of the child $i$ instead of the *minimum* key in the subtree of the child $(i + 1)$. This lets us not fetch any other nodes after we reach a leaf (in the B+ tree, all keys in the leaf node may be less than the search key, so we need to go to the next leaf node to fetch its first element).

We also use a node size of $B=32$, which is smaller than typical. The reason why it is not $16$, which was [optimal for the S+ tree](s-tree/#modifications-and-further-optimizations), is because we have the additional overhead associated with fetching the pointer, and the benefit of reducing the tree height by ~20% outweighs the cost of processing twice the elements per node, and also because it improves the running time of the `insert` query that needs to perform a costly node split every $\frac{B}{2}$ insertions on average.

<!--

We will discuss other node sizes later.

This is needed simd to be efficient (we will discuss other node sizes later).

There is some overhead, so it makes sense to use more than one cache line.

Analogous to the B+ tree,

-->

### Memory Layout

Although this is probably not the best approach in terms of software engineering, we will simply store the entire tree in a large pre-allocated array, without discriminating between leaves and internal nodes:

```c++
const int R = 1e8;
alignas(64) int tree[R];
```

We also pre-fill this array with infinities to simplify the implementation:

```c++
for (int i = 0; i < R; i++)
    tree[i] = INT_MAX;
```

(In general, it is technically cheating to compare against `std::set` or other structures that use `new` under the hood, but memory allocation and initialization are not the bottlenecks here, so this does not significantly affect the evaluation.)

Both nodes types store their keys sequentially in sorted order and are identified by the index of its first key in the array:

- A leaf node has up to $(B - 1)$ keys, but is padded to $B$ elements with infinities.
- An internal node has up to $(B - 2)$ keys padded to $B$ elements and up to $(B - 1)$ indices of its child nodes, also padded to $B$ elements.

These design decisions are not arbitrary:

- Padding ensures that leaf nodes occupy exactly 2 cache lines and internal nodes occupy exactly 4 cache lines.
- We specifically use [indices instead of pointers](/hpc/cpu-cache/pointers/) to save cache space.
- We store indices right after the keys even though they are stored in separate cache lines because [we have reasons](/hpc/cpu-cache/aos-soa/).
- We intentionally "waste" one array cell in leaf nodes and $2+1=3$ cells in internal nodes because we need it to store temporary results during a node split.

Initially, we only have one empty leaf node as the root:

```c++
const int B = 32;

int root = 0;   // where the keys of the root start
int n_tree = B; // number of allocated array cells
int H = 1;      // current tree height
```

To "allocate" a new node, we simply increase `n_tree` by $B$ if it is a leaf node or by $2 B$ if it is an internal node. 

Since new nodes can only be created by splitting a full node, each node except for the root will be at least half full. This implies that we need between 4 and 8 bytes per integer element (the internal nodes will contribute $\frac{1}{16}$-th or so to that number), the former being the case when the inserts are sequential, and the latter being the case when the input is adversarial. When the queries are uniformly distributed, the nodes are ~75% full on average, projecting to ~5.2 bytes per element.

B-trees are very memory-efficient compared to the pointer-based binary trees. For example, `std::set` needs at least three pointers (the left child, the right child, and the parent), alone costing $3 \times 8 = 24$ bytes, plus at least another $8$ bytes to store the key and the meta-information due to [structure padding](hpc/cpu-cache/alignment/).

### Searching

We used permutations when we implemented [S-trees](../s-tree/#optimization). Storing values in permuted order will make inserts much harder, so we change the approach.

Using popcount instead of tzcnt: the index i is equal to the number of keys less than x, so we can compare x against all keys, combine the vector mask any way we want, call `maskmov`, and then calculate the number of set bits with popcnt. This removes the need to store the keys in any particular order, which lets us skip the permutation step and also use this procedure on the last layer as well.

```c++
typedef __m256i reg;

reg cmp(reg x, int *node) {
    reg y = _mm256_load_si256((reg*) node);
    return _mm256_cmpgt_epi32(x, y);
}

unsigned rank32(reg x, int *node) {
    reg m1 = cmp(x, node);
    reg m2 = cmp(x, node + 8);
    reg m3 = cmp(x, node + 16);
    reg m4 = cmp(x, node + 24);

    m1 = _mm256_blend_epi16(m1, m2, 0b01010101);
    m3 = _mm256_blend_epi16(m3, m4, 0b01010101);
    m1 = _mm256_packs_epi16(m1, m3);

    unsigned mask = _mm256_movemask_epi8(m1);
    return __builtin_popcount(mask);    
}
```

This is also the reason why the "key area" in the nodes should not be contaminated and only store keys padded with infinities — or masked out.

To implement `lower_bound`, we just use the same procedure, but fetch the pointer after we computed the child number:

```c++
int lower_bound(int _x) {
    unsigned k = root;
    reg x = _mm256_set1_epi32(_x);
    
    for (int h = 0; h < H - 1; h++) {
        unsigned i = rank32(x, &tree[k]);
        k = tree[k + B + i];
    }

    unsigned i = rank32(x, &tree[k]);

    return tree[k + i]; // what if next block? maybe we store 31 elements?
}
```

Implementing `lower_bound` is easy, and it doesn't introduce much overhead. The hard part is to implement insertion.

### Insertion

Insertion needs a lot of logic, but the good news is that it does not have to be executed frequently.

Most of the time, all we need is to reach a leaf node and then insert a key into it, moving some other keys one position to the right.

Occasionally, we also need to split the node and/or update some parents, but this is relatively rare, so let's focus on the most common part.

To insert efficiently.

```c++
struct Precalc {
    alignas(64) int mask[B][B];

    constexpr Precalc() : mask{} {
        for (int i = 0; i < B; i++)
            for (int j = i; j < B - 1; j++)
                mask[i][j] = -1;
    }
};

constexpr Precalc P;
```

```c++
void insert(int *node, int i, int x) {
    for (int j = B - 8; j >= 0; j -= 8) {
        reg t = _mm256_load_si256((reg*) &node[j]);
        reg mask = _mm256_load_si256((reg*) &P.mask[i][j]);
        _mm256_maskstore_epi32(&node[j + 1], mask, t);
    }
    node[i] = x;
}
```

Next, let's try. To split a node, we need. So let's write another primitive:

```c++
// move the second half of a node and fill it with infinities
void move(int *from, int *to) {
    const reg infs = _mm256_set1_epi32(INT_MAX);
    for (int i = 0; i < B / 2; i += 8) {
        reg t = _mm256_load_si256((reg*) &from[B / 2 + i]);
        _mm256_store_si256((reg*) &to[i], t);
        _mm256_store_si256((reg*) &from[B / 2 + i], infs);
    }
}
```

Now we need to (very carefully)

```c++
void insert(int _x) {
    // we save the path we visited in case we need to update some of our ancestors
    unsigned sk[10], si[10];
    
    unsigned k = root;
    reg x = _mm256_set1_epi32(_x);

    for (int h = 0; h < H - 1; h++) {
        unsigned i = rank32(x, &tree[k]);

        // check if we need to update the key right away
        tree[k + i] = (_x > tree[k + i] ? _x : tree[k + i]);
        sk[h] = k, si[h] = i; // and save the path
        
        k = tree[k + B + i];
    }

    unsigned i = rank32(x, &tree[k]);

    // we can start computing this check ahead of insertion
    bool filled  = (tree[k + B - 2] != INT_MAX);

    insert(tree + k, i, _x);

    if (filled) {
        // create a new leaf node
        move(tree + k, tree + n_tree);
        
        int v = tree[k + B / 2 - 1]; // new key to be inserted
        int p = n_tree;              // pointer to the newly created node
        
        n_tree += B;

        for (int h = H - 2; h >= 0; h--) {
            // for each parent node we repeat this process
            // until we reach the root of determine that the node is not split
            k = sk[h], i = si[h];

            filled = (tree[k + B - 3] != INT_MAX);

            // the node already has a correct key (right one)
            //                  and a correct pointer (left one)
            insert(tree + k,     i,     v);
            insert(tree + k + B, i + 1, p);
            
            if (!filled)
                return; // we're done

            // create a new internal node
            move(tree + k,     tree + n_tree);     // move keys
            move(tree + k + B, tree + n_tree + B); // move pointers

            v = tree[k + B / 2 - 1];
            tree[k + B / 2 - 1] = INT_MAX;

            p = n_tree;
            n_tree += 2 * B;
        }

        // if we've reached here, this means we've reached the root, and it was split
        tree[n_tree] = v;

        tree[n_tree + B] = root;
        tree[n_tree + B + 1] = p;

        root = n_tree;
        n_tree += 2 * B;
        H++;
    }
}
```

There are many inefficiencies, but luckily they are rarely called.

## Evaluation

We need to implement `insert` and `lower_bound`. Deletions, iteration, and other things are not our concern for now.

Of course, this comparison is not fair, as implementing a dynamic search tree is a more high-dimensional problem.

Technically, we use `std::multiset` and `absl::btree_multiset` to support repeated keys.

Keys are uniform, but we should not rely on that fact (e. g. using ).

It is common that >90% of operations are lookups. Optimizing searches is important because every other operation starts with locating a key.

(a different set each time)

We use different points between $10^4$ and $10^7$ in (arount 250 in total). After, we use $10^6$ queries (independently random each time). All data is generated uniformly in the range $[0, 2^{30})$ and independent between stages.

$1.17^k$ and $1.17^{k+1}$.

It may or may not be representative of your use case.

[Hugepages](/hpc/cpu-cache/paging) are enabled globally for all three algorithms.

As predicted, the performance is much better:

![](../img/btree-absolute.svg)

When the data set is small, the latency increases in discrete steps: 3.5ns for under 32 elements, 6.5ns, and to 12ns, until it hits the L2 cache (not shown on graphs) and starts increasing more smoothly yet still with noticeable spikes when the tree grows upwards.

![](../img/btree-relative.svg)

I apologize to everyone else, but this is sort of your fault for not using a public benchmark.

![](../img/btree-absl.svg)

Interestingly, B− tree wins over `absl::btree` even when it only stores one key: it takes around 5ns to figure out branch prediction, while B− tree is branchless.

I don't know (yet) why insertions are *that* slow. My guess is that it has something to do with data dependencies between queries.

### Possible Optimizations

Maximum height was 6.

Compile. I tried it, but couldn't get the compiler to generate optimal code.

The idiomatic C++ way is to use virtual functions, but we will be explicit:

```c++
void (*insert_ptr)(int);
int (*lower_bound_ptr)(int);

void insert(int x) {
    insert_ptr(x);
}

int lower_bound(int x) {
    return lower_bound_ptr(x);
}
```

```c++
template <int H>
void insert_impl(int _x) {
    // ...
}

template <int H>
void insert_impl(int _x) {
    // ...
    if (/* tree grows */) {
        // ...
        insert_ptr = &insert_impl<H + 1>;
        lower_bound_ptr = &lower_bound_impl<H + 1>;
    }
}

template <>
void insert_impl<10>(int x) {
    std::cerr << "This depth was not supposed to be reached" << std::endl;
    exit(1);
}
```

```c++
insert_ptr = &insert_impl<1>;
lower_bound_ptr = &lower_bound_impl<1>;
```

Recursion unrolled.

It is possible to get rid of pointers even more. For example, for large trees, we can probably afford a small S+ tree for $16 \cdot 17$ or so elements as the root, which we rebuild from scratch on each infrequent occasion when it changes.

### Other Operations

Going to father and fetching $B$ pointers at a time is faster as it negates [pointer chasing](/hpc/cpu-cache/latency/).

Pointer to either parent or next node.

Stack of ancestors.

Nodes are at least ½ full (because they are created ½ full), except for the root, and, on average, ¾ full assuming random inserts.

We can't store junk in keys.

B* split

If the node is at least half-full, we're done. Otherwise, we try to borrow keys from siblings (no expensive two-pointer merging is necessary: we can just append them to the end/beginning and swap key of the parent).

If that fails, we can merge the two nodes together, and iteratively delete the key in the parent.

One interesting use case is *rope*, also known as *cord*, which is used for wrapping strings in a tree to support mass operations. For example, editing a very large text file. Which is the topic.

[Skip list](https://en.wikipedia.org/wiki/Skip_list), which [some attempts to vectorize it](https://doublequan.github.io/), although it may achieve higher total throughput in concurrent setting. I have low hope that it can be improved.

## Acknowledgements

Thanks to [Danila Kutenin](https://danlark.org/) from Google for meaningful discussions of applicability and possible replacement in Abseil.
