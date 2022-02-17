---
title: Static B-Trees
weight: 2
draft: true
---

This article is a follow-up on the [previous one](../binary-search), where we optimized binary search by the means of removing branching and improving the memory layout. Here, we will also be searching over sorted arrays, but this time we are not limited to fetching and comparing only one element at a time.

In this article, we generalize the techniques we developed for binary search to *static B-trees* and accelerate them further using [SIMD instructions](/hpc/simd). In particular, we develop two new implicit data structures:

- The [first one](#b-tree-layout) is based on the memory layout of a B-tree, and, depending on the array size, it is up to 8x faster than `std::lower_bound` while using the same space as the array and only requiring a permutation of its elements.
- The [second one](#b-tree-layout-1) is based on the memory layout of a B+ tree, and it is up to 15x faster that `std::lower_bound` while using just 6-7% more memory — or 6-7% **of** the memory if we can keep the original sorted array.

To distinguish them from B-trees — the structures with pointers, thousands to millions of elements per node, and empty spaces — we will use the names *S-tree* and *S+ tree* respectively to refer to these particular memory layouts[^name].

[^name]: [Similar to B-trees](https://en.wikipedia.org/wiki/B-tree#Origin), "the more you think about what the S in S-trees means, the better you understand S-trees."

<!--

Similar to how the B in B-trees stands for many thing in We even have more claim to it than Bayer had on B-tree: it is succinct, static, simd, my name, my surname.

- *S-tree*: an approach based on the implicit (pointer-free) B-layout accelerated with SIMD operations to perform search efficiently while using less memory bandwidth and is ~8x faster on small arrays and 5x faster on large arrays.
- *S+ tree*: an approach similarly based on the B+ layout and achieves up to 15x faster for small arrays and ~7x faster on large arrays. Uses 6-7% of the array memory.

There is a an obscure data structure in computer vision.

The last two approaches use SIMD, which technically disqualifies it from being binary search. This is technically not a drop-in replacement, since it requires some preprocessing, but I can't recall a lot of scenarios where you obtain a sorted array but can't spend linear time on preprocessing.

-->

To the best of my knowledge, this is a significant improvement over the existing [approaches](http://kaldewey.com/pubs/FAST__SIGMOD10.pdf). As before, we are using Clang 10 targeting a Zen 2 CPU, but the relative performance improvements should approximately transfer to other platforms, including Arm-based chips.

<!--

This is a large article, which will turn into a multi-hour read. If you feel comfortable reading [intrinsic](/hpc/simd/intrinsics)-heavy code without any context whatsoever, you can skim through the first four implementation and jump straight to the last section.

-->

## B-Tree Layout

B-trees generalize the concept of binary search trees by allowing nodes to have more than two children. Instead of a single key, a node of a B-tree of order $k$ can contain up to $B = (k - 1)$ keys that are stored in sorted order and up to $k$ pointers to child nodes, each satisfying the property that all keys in the subtrees of the first $i$ children are not greater than the $i$-th key in the parent node.

![A B-tree of order 4](../img/b-tree.jpg)

The main advantage of this approach is that it reduces the tree height by $\frac{\log_2 n}{\log_k n} = \frac{\log k}{\log 2} = \log_2 k$ times, while fetching each node still takes roughly the same time as long it fits into a single [memory block](/hpc/external-memory/hierarchy/).

B-trees were primarily developed for the purpose of managing on-disk databases, where the latency of a randomly fetching a single byte is comparable with the time it takes to read the next 1MB of data sequentially. For our use case, we will be using the block size of $B = 16$ elements — or $64$ bytes, the size of the cache line — which makes the tree height and the total number of cache line fetches per query $\log_2 17 \approx 4$ times smaller compared to the binary search.

### Implicit B-Tree

Storing and fetching pointers in a B-tree node wastes precious cache space and decreases performance, but they are essential for changing the tree structure on inserts and deletions. But when there are no updates, and the structure of a tree is *static*, we can get rid of the pointers, which makes the structure *implicit*.

One of the ways to achieve this is by generalizing the [Eytzinger numeration](../binary-search#eytzinger-layout) to $(B + 1)$-ary trees:

- The root node is numbered $0$.
- Node $k$ has $(B + 1)$ child nodes numbered $\\{k \cdot (B+1) + i\\}$ for $i \in [1, B]$.

This way we can only use $O(1)$ additional memory by allocating one large two-dimensional array of keys and relying on index arithmetic to locate children nodes in the tree:

```c++
const int B = 16;

int nblocks = (n + B - 1) / B;
int btree[nblocks][B];

int go(int k, int i) { return k * (B + 1) + i + 1; }
```

<!-- todo: exact height -->

This numeration automatically makes the B-tree complete or almost complete with the height of $\Theta(\log_{B + 1} n)$. If the length of the initial array is not a multiple of $B$, the last block is padded with the largest value of its data type.

### Construction

We can construct B-tree similar to how we constructed the Eytzinger array — by traversing the search tree:

```c++
void build(int k = 0) {
    static int t = 0;
    if (k < nblocks) {
        for (int i = 0; i < B; i++) {
            build(go(k, i));
            btree[k][i] = (t < n ? a[t++] : INT_MAX);
        }
        build(go(k, B));
    }
}
```

It is correct because each value of the initial array will be copied to a unique position in the resulting array, and the tree height is $\Theta(\log_{B+1} n)$ because $k$ is multiplied by $(B + 1)$ each time we descend into a child node.

Note that this numeration causes a slight imbalance: left-er children may have larger subtrees, although this is only true for $O(\log_{B+1} n)$ parent nodes.

### Searches

To find the lower bound, we need to fetch the $B$ keys in a node, find the first key $a_i$ not less than $x$, descend to the $i$-th child — and continue until we reach a leaf node. There is some variability in how to find that first key. For example, we could do a tiny internal binary search that makes $O(\log B)$ iterations, or maybe just compare each key sequentially in $O(B)$ time until we find the local lower bound, hopefully exiting from the loop a bit early.

But we are not going to do that — because we can use [SIMD](/hpc/simd). It doesn't work well with branching, so essentially what we want to do is to compare against all $B$ elements regardless, compute a bit mask out of these comparisons, and then use the `ffs` instruction to find the bit corresponding to the first non-lesser element:

```cpp
int mask = (1 << B);

for (int i = 0; i < B; i++)
    mask |= (btree[k][i] >= x) << i;

int i = __builtin_ffs(mask) - 1;
// now i is the number of the correct child node
```

Unfortunately, the compilers are not smart enough yet to auto-vectorize this code, so we need to manually use intrinsics:

```c++
typedef __m256i reg;

int cmp(reg x_vec, int* y_ptr) {
    reg y_vec = _mm256_load_si256((reg*) y_ptr); // load 8 sorted elements
    reg mask = _mm256_cmpgt_epi32(x_vec, y_vec); // compare against the key
    return _mm256_movemask_ps((__m256) mask);    // extract the 8-bit mask
}
```

This function works for 8-element vectors, which is half our block / cache line size. To process the entire block, we need to call it twice and then combine the masks:

```c++
int mask = ~(
    cmp(x, &btree[k][0]) +
    (cmp(x, &btree[k][8]) << 8)
);
```

Now, to descend down the tree, we use `ffs` on that mask to get the correct child number and just call the `go` function we defined before:

```c++
int i = __builtin_ffs(mask) - 1;
k = go(k, i);
```

To actually return the result in the end, we'd want to just fetch `btree[k][i]` in the last node we visited, but the problem is that sometimes the local lower bound doesn't exist ($i \ge B$) because $x$ happens to be greater than all the keys in the node. We could, in theory, do the same thing we did for the [Eytzinger binary search](../binary-search/#search-implementation) and restore the correct element *after* we calculate the last index, but we don't have a nice bit trick this time and have to do a lot of [divisions by 17](/hpc/arithmetic/division) to compute it, which will be slow and almost certainly not worth it.

Instead, we can just remember and return the last local lower bound we encountered when we descended the tree:

```c++
int lower_bound(int _x) {
    int k = 0, res = INT_MAX;
    reg x = _mm256_set1_epi32(_x);
    while (k < nblocks) {
        int mask = ~(
            cmp(x, &btree[k][0]) +
            (cmp(x, &btree[k][8]) << 8)
        );
        int i = __builtin_ffs(mask) - 1;
        if (i < B)
            res = btree[k][i];
        k = go(k, i);
    }
    return res;
}
```

This implementation outperforms all previous binary search implementations, and by a huge margin:

![](../img/search-btree.svg)

This is very good — but we can optimize it even further.

### Optimization

Before everything else, let's allocate the memory for the array on a [huge page](/hpc/cpu-cache/paging):

```c++
const int P = 1 << 21;                        // page size in bytes (2MB)
const int T = (64 * nblocks + P - 1) / P * P; // can only allocate whole number of pages
btree = (int(*)[16]) std::aligned_alloc(P, T);
madvise(btree, T, MADV_HUGEPAGE);
```

This slightly improves the performance on larger array sizes:

![](../img/search-btree-hugepages.svg)

Ideally, we'd also need to enable hugepages for all [previous implementations](../binary-search) to make the comparison fair, but it doesn't matter that much because they all have some form of prefetching that alleviates this problem.

With that settled, let's begin real optimization. First of all, we'd want to use compile-time constants instead of variables as much as possible because it lets the compiler embed them in the machine code, unroll loops, optimize arithmetic, and do all sorts of other nice stuff for us for free. Specifically, we want to know the tree height in advance:

<!-- todo: maybe this can be computed simpler? -->

```c++
constexpr int height(int n) {
    // grow the tree until its size exceeds n elements
    int s = 0, // total size so far
        l = B, // size of the next layer
        h = 0; // height so far
    while (s + l - B < n) {
        s += l;
        l *= (B + 1);
        h++;
    }
    return h;
}

const int H = height(N);
```

<!--

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
    int r = (n - s + B - 1) / B; // remaining blocks on the last layer
    return {h, s / B + (r + B) / (B + 1) * (B + 1)};
}

const int [height, nblocks] = precalc(N);
```

-->

Next, we can find the local lower bound in nodes faster. Instead of calculating it separately for two 8-element blocks and merging masks, we can use one [packs](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=3037,4870,6715,4845,3853,90,7307,5993,2692,6946,6949,5456,6938,5456,1021,3007,514,518,7253,7183,3892,5135,5260,3915,4027,3873,7401,4376,4229,151,2324,2310,2324,4075,6130,4875,6385,5259,6385,6250,1395,7253,6452,7492,4669,4669,7253,1039,1029,4669,4707,7253,7242,848,879,848,7251,4275,879,874,849,833,6046,7250,4870,4872,4875,849,849,5144,4875,4787,4787,4787,5227,7359,7335,7392,4787,5259,5230,5223,6438,488,483,6165,6570,6554,289,6792,6554,5230,6385,5260,5259,289,288,3037,3009,590,604,5230,5259,6554,6554,5259,6547,6554,3841,5214,5229,5260,5259,7335,5259,519,1029,515,3009,3009,3011,515,6527,652,6527,6554,288,3841,5230,5259,5230,5259,305,5259,591,633,633,5259,5230,5259,5259,3017,3018,3037,3018,3017,3016,3013,5144&text=_mm256_packs_epi32&techs=AVX,AVX2) instruction before the `movemask`:

```c++
unsigned rank(reg x, int* y) {
    reg a = _mm256_load_si256((reg*) y);
    reg b = _mm256_load_si256((reg*) (y + 8));

    reg ca = _mm256_cmpgt_epi32(a, x);
    reg cb = _mm256_cmpgt_epi32(b, x);

    reg c = _mm256_packs_epi32(ca, cb);
    int mask = _mm256_movemask_epi8(c);

    // we need to divide the result by two because we call movemask_epi8 on 16-bit masks:
    return __tzcnt_u32(mask) >> 1;
}
```

This instruction converts 32-bit integers stored in two registers to 16-bit integers stored in one register — in our case, effectively joining the vector masks into one. Note that we've swapped the order of comparison — this lets us not invert the mask in the end, but we have to subtract one from the search key once in the beginning to make it correct (otherwise it works as `upper_bound`).

The problem is, it does this weird interleaving where the result is written in the `a1 b1 a2 b2` order instead of `a1 a2 b1 b2` that want. To correct this, we need to [permute](/hpc/simd/shuffling) the resulting vector, but instead of doing this during the query time, we can just permute every node during preprocessing:

```c++
void permute(int *node) {
    const reg perm = _mm256_setr_epi32(4, 5, 6, 7, 0, 1, 2, 3);
    reg* middle = (reg*) (node + 4);
    reg x = _mm256_loadu_si256(middle);
    x = _mm256_permutevar8x32_epi32(x, perm);
    _mm256_storeu_si256(middle, x);
}
```

We just call `permute(&btree[k])` right after we are done with building a node. There are probably faster ways to swap middle elements, but we will leave it here, as the preprocessing time is not important for now.

This new SIMD routine is significantly faster because the extra `movemask` was slow and also blending the two masks took quite a few instructions. Unfortunately, we now can't just do the `res = btree[k][i]` update anymore because the elements are permuted. We can solve this problem with some bit-level trickery in terms of `i`, but indexing a small lookup table turns out to be faster and also doesn't require a new branch:

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

This `update` procedure takes some time, but it's not on the critical path between the iterations, so it doesn't affect the actual performance that much.

Stitching it all together (and leaving out some other minor optimizations):

```c++
int lower_bound(int _x) {
    int k = 0, res = INT_MAX;
    reg x = _mm256_set1_epi32(_x - 1);
    for (int h = 0; h < H - 1; h++) {
        unsigned i = rank(x, &btree[k]);
        update(res, &btree[k], i);
        k = go(k, i);
    }
    // the last branch:
    if (k < nblocks) {
        unsigned i = rank(x, btree[k]);
        update(res, &btree[k], i);
    }
    return res;
}
```

All this work saved us 15-20% or so:

![](../img/search-btree-optimized.svg)

Doesn't feel very satisfying so far, but we will reuse these optimization ideas later.

There are two main problems with the current implementation:

- The `update` procedure as is quite costly, especially considering that it is likely to be useless: 16 out of 17 times we can just fetch the result from the last block.
- We do non-constant number of iterations, causing branch prediction problems similar to how it did for the [Eytzinger binary search](/binary-search/#removing-the-last-branch); you can also see it on the graph this time, but the latency bumps have a period of $2^4$.

To address these problems, we need to change the layout a little bit.

## B+ Tree Layout

The layout is not succinct: we need about some additional memory to store the internal nodes — about $\frac{1}{16}$-th of the original array size, to be exact.

B-tree layout

We will explain the constexpr functions because this time it is important:

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
```

To be more explicit with pointer arithmetic, the tree is just a single array now:

```c++
int *btree;
```

```c++
    for (int i = N; i < S; i++)
        btree[i] = INT_MAX;

    memcpy(btree, a, 4 * N);
    
    for (int h = 1; h < H; h++) {
        for (int i = 0; i < offset(h + 1) - offset(h); i++) {
            int k = i / B,
                j = i - k * B;
            k = k * (B + 1) + j + 1; // compare right
            // and then always to the left
            for (int l = 0; l < h - 1; l++)
                k *= (B + 1);
            btree[offset(h) + i] = (k * B < N ? btree[k * B] : INT_MAX);
        }
    }

    for (int i = offset(1); i < S; i += B)
        permute(btree + i);
}
```

```c++
int lower_bound(int _x) {
    unsigned k = 0;
    reg x = _mm256_set1_epi32(_x - 1);
    for (int h = H - 1; h > 0; h--) {
        unsigned i = permuted_rank(x, btree + offset(h) + k);
        k = k * (B + 1) + i * B;
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

<!--

Bloated:

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

```c++
unsigned rank32(reg x, int *node) {
    unsigned mask = cmp(x, node)
                  | (cmp(x, node + 8) << 8)
                  | (cmp(x, node + 16) << 16)
                  | (cmp(x, node + 24) << 24);
```

-->

Another idea is to use cache more efficiently. For example, you can execute `_mm256_stream_load_si256` on just the last iteration.

They aren't beneficial for throughput:

![](../img/search-bplus-other.svg)

However, they perform better:

![](../img/search-latency-bplus.svg)

## Conclusions

![](../img/search-all.svg)

It may or may not be beneficial to reverse the order in which layers are stored. I only implemented right-to-left because that was easier to code.

### As a Dynamic Tree

When we compare S+ trees to `std::set` where we add the same elements and search for the same lower bounds (not counting the time it took to add them), the comparison is even more favorable:

![](../img/search-set-relative.svg)

My next priorities is to adapt it to segment trees, which I know how to do, and to B-trees, which I don't exactly know how to do. But comparing to `std::set` hints that there may be up to 30x improvements:

`absl::btree_set`, the only widely-used B-tree implementation I know, is just slightly faster than binary search.

![](../img/search-set-relative-all.svg)

A ~15x improvement is definitely worth it — and the memory overhead is not large, as we only need to store pointers (indices, actually) for internal nodes. It may be higher, because we need to fetch two separate memory blocks, or lower, because we need to handle updates somehow. Either way, this will be an interesting optimization problem.

That's it. This implementation should outperform even the [state-of-the-art indexes](http://kaldewey.com/pubs/FAST__SIGMOD10.pdf) used in high-performance databases, though it's mostly due to the fact that data structures used in real databases have to support fast updates while we don't.

The problem has more dimensions.

NEON would require some [trickery](https://github.com/WebAssembly/simd/issues/131)

Note that this implementation is very specific to the architecture. Older CPUs and CPUs on mobile devices don't have 256-bit wide registers and will crash (but they likely have 128-bit SIMD so the loop can still be split in 4 parts instead of 2), non-Intel CPUs have their own instruction sets for SIMD, and some computers even have different cache line size.

### Acknowledgements

This [StackOverflow answer](https://stackoverflow.com/questions/20616605/using-simd-avx-sse-for-tree-traversal) by Cory Nelson is where I took the permuted SIMD routine.

<!--

I stole some pictures from blogs and I can't find the originals.

-->


