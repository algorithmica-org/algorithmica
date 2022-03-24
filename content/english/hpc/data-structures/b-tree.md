---
title: Search Trees
weight: 3
draft: true
---

In the [previous article](../s-tree), we designed *static* B-trees (*S-trees*), and we [briefly discussed](../s-tree/#as-a-dynamic-tree) how to turn them *dynamic* while retaining performance gains from [SIMD](/hpc/simd).

In this article

The problem is multi-dimensional.

Of course, this comparison is not fair, as implementing a dynamic search tree is a more high-dimensional problem.

We’d also need to implement the update operation, which will not be that efficient, and for which we’d need to sacrifice the fanout factor. But it still seems possible to implement a 10-20x faster std::set and a 3-5x faster absl::btree_set, depending on how you define “faster” — and this is one of the things we’ll attempt to do next.

Static as

![](../img/btree-absolute.svg)

![](../img/btree-relative.svg)

![](../img/btree-absl.svg)

When the data set is small, the latency increases in discrete steps: 3.5ns for under 32 elements, 6.5ns, and to 12ns, until it hits the L2 cache (not shown on graphs) and starts increasing more smoothly yet still with noticeable spikes when the tree grows upwards.

One interesting use case is rope, also known as cord, which is used for wrapping strings in a tree to support mass operations. For example, editing a very large text file. Which is the topic.

It is common that >90% of operations are lookups. Optimizing searches is important because every other operation starts with locating a key.

I don't know (yet) why insertions are *that* slow. My guess is that it has something to do with data dependencies between queries.

I apologize to everyone else, but this is sort of your fault for not using a public benchmark.

## B− Tree

[B+ tree](../s-tree/#b-tree-layout-1).

B− ("B minus") tree. The difference is:

- We are specifically storing the *last* element. This is needed
- We use a small node size $B=32$. This is needed simd to be efficient (we will discuss other node sizes in the future)
- We don't store any pointers except for the children (while B+ stores one pointer for the next leaf node).

The difference is that 

### Layout

To simplify memory all with infinities.

```c++
const int B = 32;
int H = 1; // tree height

const int R = 1e8; // reserve

alignas(64) int tree[R];
int n_tree = B; // 31 (+ 1) + 32 for internal nodes and 31 for data nodes
int root = 0;

for (int i = 0; i < R; i++)
    tree[i] = INT_MAX;
```

To "allocate" a new node, we simply increase `n_tree` by $B$ if it is a data node or by $2 \cdot B$ if it is an internal node. 

### Searching

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

```c++
int lower_bound(int _x) {
    //std::cerr << std::endl << "lb " << _x << std::endl;
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

### Insertions

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

// move the second half of a node and fill it with infinities
void move(int *from, int *to) {
    const reg infs = _mm256_set1_epi32(INT_MAX);
    for (int i = 0; i < B / 2; i += 8) {
        reg t = _mm256_load_si256((reg*) &from[B / 2 + i]);
        _mm256_store_si256((reg*) &to[i], t);
        _mm256_store_si256((reg*) &from[B / 2 + i], infs); // probably not necessary for pointers
    }
}
```

```c++
void insert(int _x) {
    unsigned sk[20], si[20];
    
    unsigned k = root;
    reg x = _mm256_set1_epi32(_x);

    for (int h = 0; h < H - 1; h++) {
        unsigned i = rank32(x, &tree[k]);
        sk[h] = k, si[h] = i;
        k = tree[k + B + i];
    }

    unsigned i = rank32(x, &tree[k]);

    bool filled  = (tree[k + B - 2] != INT_MAX);
    bool updated = (tree[k + i]     == INT_MAX);

    insert(tree + k, i, _x);

    if (updated) {
        for (int h = H - 2; h >= 0; h--) {
            int idx = sk[h] + si[h];
            tree[idx] = (tree[idx] < _x ? _x : tree[idx]);
        }
    }

    if (filled) {
        // create a new leaf node
        move(tree + k, tree + n_tree);
        
        int v = tree[k + B / 2 - 1]; // new key to be inserted
        int p = n_tree;              // pointer to the newly created node
        
        n_tree += B;

        for (int h = H - 2; h >= 0; h--) {
            k = sk[h], i = si[h];

            filled = (tree[k + B - 3] != INT_MAX);

            // the node already has a correct key (right one) and a correct pointer (left one) 
            insert(tree + k,     i,     v);
            insert(tree + k + B, i + 1, p);
            
            if (!filled)
                return;

            // create a new internal node
            move(tree + k,     tree + n_tree);     // move keys
            move(tree + k + B, tree + n_tree + B); // move pointers

            v = tree[k + B / 2 - 1];
            tree[k + B / 2 - 1] = INT_MAX;

            p = n_tree;
            n_tree += 2 * B;
        }

        if (filled) {
            // tree grows

            tree[n_tree] = v;

            tree[n_tree + B] = root;
            tree[n_tree + B + 1] = p;

            root = n_tree;
            n_tree += 2 * B;
            H++;
        }
    }
}
```

## Optimizations

...

## Acknowledgements

Thanks to Danila Kutenin for meaningful discussions of applicability.
