---
title: Static B-Trees
weight: 2
draft: true
---

This is a follow up on the [previous article](../binary-search) about optimizing binary search. For more context, go there first.

- *S-tree*: an approach based on the implicit (pointer-free) B-layout accelerated with SIMD operations to perform search efficiently while using less memory bandwidth and is ~8x faster on small arrays and 5x faster on large arrays.
- *S+ tree*: an approach similarly based on the B+ layout and achieves up to 15x faster for small arrays and ~7x faster on large arrays. Uses 6-7% of the array memory.

The last two approaches use SIMD, which technically disqualifies it from being binary search. This is technically not a drop-in replacement, since it requires some preprocessing, but I can't recall a lot of scenarios where you obtain a sorted array but can't spend linear time on preprocessing. But otherwise they are effectively drop-in replacements to `std::lower_bound`.

The more you think about the name. "S-tree" and "S+ tree" respectively. There is a an obscure data structures in computer vision. We even have more claim to it than Boer had on B-tree: it is succinct, static, simd, my name, my surname.

## B-Tree Layout

We aren't limited to fetching one element at a time and comparing it.

B-trees are basically $(k+1)$-ary trees, meaning that they store $k$ elements in each node and choose between $(k+1)$ possible branches instead of 2.

They are widely used for indexing in databases, especially those that operate on-disk, because if $k$ is big, this allows large sequential memory accesses while reducing the height of the tree.

To perform static binary searches, one can implement a B-tree in an implicit way, i. e. without actually storing any pointers and spending only $O(1)$ additional memory, and $k$ could be made equal to the cache line size so that each node request fetches exactly one cache line.

![A B-tree of order 4](../img/b-tree.jpg)

Let's assume that arithmetic costs nothing and do simple cache block analysis:

* The Eytzinger binary search is supposed to be $4$ times faster if compute didn't matter, as it requests them ~4 times faster on average.

* The B-tree makes $\frac{\log_{17} n}{\log_2 n} = \frac{\log n}{\log 17} \frac{\log 2}{\log n} = \frac{\log 2}{\log 17} \approx 0.245$ memory access per each request of binary search, i. e. it requests ~4 times less cache lines to fetch

This explains why they have roughly the same slope.

### B-tree layout

B-trees generalize the concept of binary search trees by allowing nodes to have more than two children.

Instead of single key, a B-tree node contains up to $B$ sorted keys may have up to $(B+1)$ children, thus reducing the tree height in $\frac{\log_2 n}{\log_B n} = \frac{\log B}{\log 2} = \log_2 B$ times.

They were primarily developed for the purpose of managing on-disk databases, as their random access times are almost the same as reading 1MB of data sequentially, which makes the trade-off between number of comparisons and tree height beneficial. In our implementation, we will make each the size of each block equal to the cache line size, which in case of `int` is 16 elements.

Normally, a B-tree node also stores $(B+1)$ pointers to its children, but we will only store keys and rely on pointer arithmetic, similar to the one used in Eytzinger array:

* The root node is numbered $0$.

* Node $k$ has $(B+1)$ child nodes numbered $\{k \cdot (B+1) + i\}$ for $i \in [1, B]$.

Keys are stored in a 2d array in non-decreasing order. If the length of the initial array is not a multiple of $B$, the last block is padded with the largest value if its data type. 

```c++
typedef __m256i reg;

const int B = 16;
const int INF = std::numeric_limits<int>::max();

int n;
int nblocks;
int *_a;
int (*btree)[B];

int go(int k, int i) { return k * (B + 1) + i + 1; }

void build(int k = 0) {
    static int t = 0;
    if (k < nblocks) {
        for (int i = 0; i < B; i++) {
            build(go(k, i));
            btree[k][i] = (t < n ? _a[t++] : INF);
        }
        build(go(k, B));
    }
}

void prepare(int *a, int _n) {
    n = _n;
    nblocks = (n + B - 1) / B;
    _a = a;
    btree = (int(*)[16]) std::aligned_alloc(64, 64 * nblocks);
    build();
}

int cmp(reg x_vec, int* y_ptr) {
    reg y_vec = _mm256_load_si256((reg*) y_ptr);
    reg mask = _mm256_cmpgt_epi32(x_vec, y_vec);
    return _mm256_movemask_ps((__m256) mask);
}

int lower_bound(int x) {
    int k = 0, res = INF;
    reg x_vec = _mm256_set1_epi32(x);
    while (k < nblocks) {
        int mask = ~(
            cmp(x_vec, &btree[k][0]) +
            (cmp(x_vec, &btree[k][8]) << 8)
        );
        int i = __builtin_ffs(mask) - 1;
        if (i < B)
            res = btree[k][i];
        k = go(k, i);
    }
    return res;
}
```


We can construct B-tree similarly by traversing the search tree.

It is correct, because each value of initial array will be copied to a unique position in the resulting array, and the tree height is $\Theta(\log_{B+1} n)$, because $k$ is multiplied by $(B + 1)$ each time a child node is created.

Note that this approach causes a slight imbalance: "lefter" children may have larger respective ranges.

So, as we promised before, we will perform all $16$ comparisons to compute the index of the right child node, but we leverage SIMD instructions to do it efficiently. Just to clarify — we want to do something like this:

```cpp
int mask = (1 << B);

for (int i = 0; i < B; i++)
    mask |= (btree[k][i] >= x) << i;

int i = __builtin_ffs(mask) - 1;
// now i is the number of the correct child node
```


…but ~8 times faster.

Actually, compiler quite often produces very optimized code that leverages these instructions for certain types of loops. This is called auto-vectorization, and this is the reason why a loop that sums up an array of `short`s is faster (theoretically by a factor of two) than the same loop for `int`s: you can fit more elements on the same 256-bit block. Sadly, this is not our case, as we have loop-carried dependencies.

The algorithm we will implement:

1. Somewhere before the main loop, convert $x$ to a vector of $8$ copies of $x$.
2. Load the keys stored in node into another 256-bit vector.
3. Compare these two vectors. This returns a 256-bit mask in which pairs that compared "greater than" are marked with ones.
4. Create a 8-bit mask out of that and return it. Then you can feed it to `__builtin_ffs`.

This is how it looks using C++ intrinsics, which are basically built-in wrappers for raw assembly instructions:


After that, we call this function two times (because our node size / cache line happens to be 512 bits, which is twice as big) and blend these masks together with bitwise operations.


That's it. This implementation should outperform even the [state-of-the-art indexes](http://kaldewey.com/pubs/FAST__SIGMOD10.pdf) used in high-performance databases, though it's mostly due to the fact that data structures used in real databases have to support fast updates while we don't.

Note that this implementation is very specific to the architecture. Older CPUs and CPUs on mobile devices don't have 256-bit wide registers and will crash (but they likely have 128-bit SIMD so the loop can still be split in 4 parts instead of 2), non-Intel CPUs have their own instruction sets for SIMD, and some computers even have different cache line size.

![](../img/search-btree.svg)

### Optimizations

Enable huge pages:

```c++
btree = (int(*)[16]) std::aligned_alloc(2 * 1024 * 1024, 64 * nblocks);
madvise(btree, 64 * nblocks, MADV_HUGEPAGE);
```

![](../img/search-btree-hugepages.svg)

```c++
constexpr std::pair<int, int> precalc(int n) {
    int s = 0, // total size
        l = B, // size of next layer
        h = 0; // height so far
    while (s + l - B < n) {
        s += l;
        l *= (B + 1);
        h++;
    }
    int r = (n - s + B - 1) / B; // remaining blocks on last layer
    return {h, s / B + (r + B) / (B + 1) * (B + 1)};
}

const int height = precalc(N).first, nblocks = precalc(N).second;
int *_a, (*btree)[B];
```

```c++
unsigned rank(reg x_vec, int* y_ptr) {
    reg a = _mm256_load_si256((reg*) y_ptr);
    reg b = _mm256_load_si256((reg*) (y_ptr + 8));

    reg ca = _mm256_cmpgt_epi32(a, x_vec);
    reg cb = _mm256_cmpgt_epi32(b, x_vec);

    reg c = _mm256_packs_epi32(ca, cb);
    int mask = _mm256_movemask_epi8(c);

    return __tzcnt_u32(mask) >> 1;    
}
```

`packs`

Or 


<!--
//const reg perm_mask = _mm256_set_epi32(3, 2, 1, 0, 7, 6, 5, 4); // todo: setr
-->


```c++
void permute(int *node) {
    const reg perm = _mm256_setr_epi32(4, 5, 6, 7, 0, 1, 2, 3);
    reg* middle = (reg*) (node + 4);
    reg x = _mm256_loadu_si256(middle);
    x = _mm256_permutevar8x32_epi32(x, perm);
    _mm256_storeu_si256(middle, x);
}
```

There are probably faster ways to swap middle elements, but we will leave it here.

You call `permute(btree[k])` after you've done with constructing a node.


```c++
const int translate[17] = {
    0, 1, 2, 3,
    8, 9, 10, 11,
    4, 5, 6, 7,
    12, 13, 14, 15,
    0
};

void update(int &res, int* node, unsigned i) {
    int val = node[translate[i]];
    res = (i < B ? val : res);
}
```

```c++
int lower_bound(int x) {
    int k = 0, res = INF;
    reg x_vec = _mm256_set1_epi32(x - 1);
    for (int h = 0; h < height - 1; h++) {
        int *node = btree[k];
        unsigned i = rank(x_vec, node);
        k = k * (B + 1) + 1; // remove + 1?
        update(res, node, i);
        k += i;
    }
    unsigned i = rank(x_vec, btree[k]);
    update(res, btree[k], i);
    int k2 = go(k, i);
    if (go(k, 0) < nblocks) {
        unsigned i = rank(x_vec, btree[k2]);
        update(res, btree[k2], i);
    }
    return res;
}
```

All that hard work is totally worth it:

![](../img/search-btree-optimized.svg)

## B+ Tree Layout

```c++
constexpr int blocks(int n) {
    return (n + B - 1) / B;
}

constexpr int prev_keys(int n) {
    return (blocks(n) + B) / (B + 1) * B;
}

constexpr int height(int n) {
    return (n <= B ? 1 : height(prev_keys(n)) + 1);
}

constexpr int offset(int h) {
    int k = 0, n = N;
    while (h--) {
        k += blocks(n) * B;
        n = prev_keys(n);
    }
    return k;
}

const int H = height(N), S = offset(H);

int *btree;

void permute(int *node) {
    const reg perm_mask = _mm256_set_epi32(3, 2, 1, 0, 7, 6, 5, 4);
    reg* middle = (reg*) (node + 4);
    reg x = _mm256_loadu_si256(middle);
    x = _mm256_permutevar8x32_epi32(x, perm_mask);
    _mm256_storeu_si256(middle, x);
}

void prepare(int *a, int n) {
    const int P = 1 << 21, T = (4 * S + P - 1) / P * P;
    btree = (int*) std::aligned_alloc(P, T);
    madvise(btree, T, MADV_HUGEPAGE);

    for (int i = N; i < S; i++)
        btree[i] = INF;

    memcpy(btree, a, 4 * N);
    
    for (int h = 1; h < H; h++) {
        for (int i = 0; i < offset(h + 1) - offset(h); i++) {
            int k = i / B,
                j = i - k * B;
            k = k * (B + 1) + j + 1; // compare right
            // and then always to the left
            for (int l = 0; l < h - 1; l++)
                k *= (B + 1);
            btree[offset(h) + i] = (k * B < N ? btree[k * B] : INF);
        }
    }

    for (int i = offset(1); i < S; i += B)
        permute(btree + i);
}

unsigned direct_rank(reg x, int* y) {
    reg a = _mm256_load_si256((reg*) y);
    reg b = _mm256_load_si256((reg*) (y + 8));

    reg ca = _mm256_cmpgt_epi32(a, x);
    reg cb = _mm256_cmpgt_epi32(b, x);

    int mb = _mm256_movemask_ps((__m256) cb);
    int ma = _mm256_movemask_ps((__m256) ca);
    
    unsigned mask = (1 << 16);
    mask |= mb << 8;
    mask |= ma;

    return __tzcnt_u32(mask);
}

unsigned permuted_rank(reg x, int* y) {
    reg a = _mm256_load_si256((reg*) y);
    reg b = _mm256_load_si256((reg*) (y + 8));

    reg ca = _mm256_cmpgt_epi32(a, x);
    reg cb = _mm256_cmpgt_epi32(b, x);

    reg c = _mm256_packs_epi32(ca, cb);
    unsigned mask = _mm256_movemask_epi8(c);

    return __tzcnt_u32(mask)/* >> 1*/;
}

int lower_bound(int _x) {
    unsigned k = 0;
    reg x = _mm256_set1_epi32(_x - 1);
    for (int h = H - 1; h > 0; h--) {
        unsigned i = permuted_rank(x, btree + offset(h) + k);
        
        //k /= B;
        //k *= (B + 1) * B;
        // k += (i << 3);
        
        k = k * (B + 1) + (i << 3);
        
        //if (N > (1 << 21) && h == 1)
        //    __builtin_prefetch(btree + k);
        
        //k += (i << 3);
    }
    unsigned i = direct_rank(x, btree + k);
    return btree[k + i];
}
```

![](../img/search-bplus.svg)

Makes more sense to look at it as a relative speedup:

![](../img/search-relative.svg)

### Measuring Actual Latency

One huge asterisk we didn't disclosed.

```c++
for (int i = 0; i < m; i++)
    checksum ^= lower_bound(q[i]);
```

To measure *actual* latency, we need to introduce a dependency between the iterations, so that the next one can't start before the previous finishes:

```c++
int last = 0;

for (int i = 0; i < m; i++) {
    last = lower_bound(q[i] ^ last);
    checksum ^= last;
}
```

![](../img/search-relative-latency.svg)


### Modifications

```c++
void permute32(int *node) {
    // a b c d 1 2 3 4 -> (a c) (b d) (1 3) (2 4) -> (a c) (1 3) (b d) (2 4)
    reg x = _mm256_load_si256((reg*) (node + 8));
    reg y = _mm256_load_si256((reg*) (node + 16));
    _mm256_storeu_si256((reg*) (node + 8), y);
    _mm256_storeu_si256((reg*) (node + 16), x);
    permute16(node);
    permute16(node + 16);
}
```

```c++
unsigned cmp(reg x, int *node) {
    reg y = _mm256_load_si256((reg*) node);
    reg mask = _mm256_cmpgt_epi32(y, x);
    return _mm256_movemask_ps((__m256) mask);
}

unsigned rank32(reg x, int *node) {
    unsigned mask = cmp(x, node)
                  | (cmp(x, node + 8) << 8)
                  | (cmp(x, node + 16) << 16)
                  | (cmp(x, node + 24) << 24);
```

```c++
unsigned permuted_rank32(reg x, int *node) {
    reg a = _mm256_load_si256((reg*) node);
    reg b = _mm256_load_si256((reg*) (node + 8));
    reg c = _mm256_load_si256((reg*) (node + 16));
    reg d = _mm256_load_si256((reg*) (node + 24));

    reg ca = _mm256_cmpgt_epi32(a, x);
    reg cb = _mm256_cmpgt_epi32(b, x);
    reg cc = _mm256_cmpgt_epi32(c, x);
    reg cd = _mm256_cmpgt_epi32(d, x);

    reg cab = _mm256_packs_epi32(ca, cb);
    reg ccd = _mm256_packs_epi32(cc, cd);
    reg cabcd = _mm256_packs_epi16(cab, ccd);
    unsigned mask = _mm256_movemask_epi8(cabcd);

    return __tzcnt_u32(mask);
}
```

Another idea is to use cache more efficiently. For example, you can execute `_mm256_stream_load_si256` on just the last iteration.

They aren't beneficial for throughput:

![](../img/search-bplus-other.svg)

However, they perform better:

![](../img/search-latency-bplus.svg)

## Conclusions

![](../img/search-all.svg)

### Acknowledgements

This [StackOverflow answer](https://stackoverflow.com/questions/20616605/using-simd-avx-sse-for-tree-traversal) by Cory Nelson is where I took the permuted SIMD routine.

<!--

I stole some pictures from blogs and I can't find the originals.

-->


