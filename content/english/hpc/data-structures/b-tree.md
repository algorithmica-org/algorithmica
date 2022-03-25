---
title: Search Trees
weight: 3
draft: true
---

In the [previous article](../s-tree), we designed *static* B-trees to speed up binary searching in sorted arrays, designing S-tree and S+ Tree. In the last section we [briefly discussed](../s-tree/#as-a-dynamic-tree) how to turn them *dynamic* while retaining performance gains from [SIMD](/hpc/simd), making a proof-of-concept. Simply adding pointers to S+ tree.

In this section, we follow up on that promise and design a minimally functional search tree for integer keys, called *B− tree*, that achieves significant improvements over [improvements](#evaluation): 7-18 times faster for large arrays and 3-8 faster for inserts. The [absl::btree](https://abseil.io/blog/20190812-btree) 3-7 times faster for searches and 1.5-2 times faster for with yet ample room for improvement.

The memory overhead of the structure around 30%. The [final implementation](https://github.com/sslotin/amh-code/blob/main/b-tree/btree-final.cc) is around 150 lines of C.

We give more details in th evaluation section.

## B− Tree

Instead of making small incremental changes, we will design just one data structure in this article, which is based on [B+ tree](../s-tree/#b-tree-layout-1) with a few minor exceptions:

- We do not store any pointers except for the children (while B+ stores one pointer for the next leaf node).
- We define key $i$ as the *maximum* key in the subtree of child $i$ instead of the *minimum* key in the subtree of child $(i + 1)$. This removes the need.
- We use a small node size $B=32$. This is needed simd to be efficient (we will discuss other node sizes later).

There is some overhead, so it makes sense to use more than one cache line.

Analogous to the B+ tree, we call this modification *B− tree*.

### Layout

We rely on arena allocation.

```c++
const int B = 32; // node size

const int R = 1e8; // reserve
alignas(64) int tree[R];

int root = 0;   // where the tree root starts
int n_tree = B; 
int H = 1;      // tree height
```

To further simplify the implementation, we set all array cells with infinities:

```c++
for (int i = 0; i < R; i++)
    tree[i] = INT_MAX;
```

We can do this — this does not affect performance. Memory allocation and initialization is not the bottleneck.

To save precious cache space, we use [indices instead of pointers](/hpc/cpu-cache/pointers/).
Despite that they are in separate cache lines, it still [makes sense](/hpc/cpu-cache/aos-soa/) to store them close to keys.

This way, leaf nodes occupy 2 cache lines and waste 1 slot, while internal nodes occupy 4 cache lines and waste 2+1=3 slots.

To "allocate" a new node, we simply increase `n_tree` by $B$ if it is a data node or by $2 \cdot B$ if it is an internal node. 

### Searching

We used permutations when we implemented [S-trees](../s-tree/#optimization). Storing values in permuted order will make inserts much harder, so we change the approach.

Using popcount instead of tzcnt: the index i is equal to the number of keys less than x, so we can compare x against all keys, combine the vector mask any way we want, call maskmov, and then calculate the number of set bits with popcnt. This removes the need to store the keys in any particular order, which lets us skip the permutation step and also use this procedure on the last layer as well.

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

As predicted, the performance is much better:

![](../img/btree-absolute.svg)

When the data set is small, the latency increases in discrete steps: 3.5ns for under 32 elements, 6.5ns, and to 12ns, until it hits the L2 cache (not shown on graphs) and starts increasing more smoothly yet still with noticeable spikes when the tree grows upwards.

![](../img/btree-relative.svg)

I apologize to everyone else, but this is sort of your fault for not using a public benchmark.

![](../img/btree-absl.svg)

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
