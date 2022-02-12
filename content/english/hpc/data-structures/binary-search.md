---
title: Searching in Sorted Arrays
weight: 1
---

The most fascinating showcases of performance engineering are not intricate 5-10% speed improvements of some databases, but multifold optimizations of some basic algorithms you can find in a textbook — the ones that are so simple that it would never even occur to try to optimize them. These kinds of optimizations are simple and instructive, and can very much be adopted elsewhere. Yet, with remarkable periodicity, these can be optimized to ridiculous levels of performance.

In this article, we will focus on such an algorithm — binary search — and significantly improve its efficiency by rearranging elements of a sorted array in a more cache-friendly way. We will develop two versions, each achieving 4-7x speedup over the standard `std::lower_bound`, depending on the cache level and available memory bandwidth:

- The first one uses what is known as *Eytzinger layout*, which is also a popular layout for other structures such as binary heaps. Our minimalistic implementation is only ~15 lines.
- The second one is its generalization based on *B-tree layout*, which is more bulky. Although it uses SIMD, which technically disqualifies it from being binary search.
- Novel structure based called S-tree based on

GCC sucked on all benchmarks, so we will be using Clang (10) exclusively. The CPU is a Zen 2, although the results should be transferrable to other platforms, including most Arm-based chips.


This is a follow up on a [previous article](https://algorithmica.org/en/eytzinger) about using Eytzinger memory layout to speed up binary search. Here we use implicit (pointerless) B-trees accelerated with SIMD operations to perform search efficiently while using less memory bandwidth.

It performs slightly worse on array sizes that fit lower layers of cache, but in low-bandwidth environments it can be up to 3x faster (or 7x faster than `std::lower_bound`).

## Binary Search

Already sorted array `t` of size `n`.

We are going ot create an array named `a` into array named `t`.

```c++
int lower_bound(int x) {
    int l = 0, r = n - 1;
    while (l < r) {
        int m = (l + r) / 2;
        if (t[m] >= x)
            r = m;
        else
            l = m + 1;
    }
    return t[l];
}
```

![](../img/search-std.svg)

This is actually how `std::lower_bound` from  works. Implementations from both [Clang](https://github.com/llvm-mirror/libcxx/blob/78d6a7767ed57b50122a161b91f59f19c9bd0d19/include/algorithm#L4169) and [GCC](https://github.com/gcc-mirror/gcc/blob/d9375e490072d1aae73a93949aa158fcd2a27018/libstdc%2B%2B-v3/include/bits/stl_algobase.h#L1023) use this metaprogramming monstrosity:

```c++
template <class _Compare, class _ForwardIterator, class _Tp>
_LIBCPP_CONSTEXPR_AFTER_CXX17 _ForwardIterator
__lower_bound(_ForwardIterator __first, _ForwardIterator __last, const _Tp& __value_, _Compare __comp)
{
    typedef typename iterator_traits<_ForwardIterator>::difference_type difference_type;
    difference_type __len = _VSTD::distance(__first, __last);
    while (__len != 0)
    {
        difference_type __l2 = _VSTD::__half_positive(__len);
        _ForwardIterator __m = __first;
        _VSTD::advance(__m, __l2);
        if (__comp(*__m, __value_))
        {
            __first = ++__m;
            __len -= __l2 + 1;
        }
        else
            __len = __l2;
    }
    return __first;
}
```

If compiler is successful in piercing through the abstractions, it compiles to roughly the same machine code and yields roughly the same performance.

We change the compiler for GCC (9.3). For some reason, it doesn't work.

```c++
int lower_bound(int x) {
    int *base = t, len = n;
    while (len > 1) {
        int half = len / 2;
        base = (base[half] < x ? &base[half] : base);
        len -= half;
    }
    return *(base + (*base < x));
}
```

```c++
int lower_bound(int x) {
    int *base = t, len = n;
    while (len > 1) {
        int half = len / 2;
        __builtin_prefetch(&base[(len - half) / 2]);
        __builtin_prefetch(&base[half + (len - half) / 2]);
        base = (base[half] < x ? &base[half] : base);
        len -= half;
    }
    return *(base + (*base < x));
}
```

### Branching

If you [run this code with perf](/hpc/analyzing-performance/profiling/), you can see that it spends most of its time waiting for a comparison to complete, which in turn is waiting for one of its operands to be fetched from memory.

To give an idea, the following code is only ~5% slower for $n \approx 10^6$:

```cpp
int slightly_slower_lower_bound(int x) {
    int l = 0, r = n - 1;
    while (l < r) {
        volatile int s = 0; // volatile to prevent compiler from cutting this code out
        for (int i = 0; i < 10; i++)
            s += i;
        int t = (l + r) / 2;
        if (a[t] >= x)
            r = t;
        else
            l = t + 1;
    }
    return a[l];
}
```

Contains an "if" that is impossible to predict better than a coin flip.

It's not illegal: ternary operator is replaced with something like `CMOV` 

<!--
int lower_bound(int x) {
    int base = 0, len = n;
    while (len > 1) {
        int half = len / 2;
        base = (a[base + half] >= x ? base : base + half);
        len -= half;
    }
    return a[base];
}
-->

![](../img/search-branchless.svg)

![](../img/search-branchless-prefetch.svg)


But this is not the largest problem. The real problem is that it waits for its operands, and the results still can't be predicted.

The running time of this (or any) algorithm is not just the "cost" of all its arithmetic operations, but rather this cost *plus* the time spent waiting for data to be fetched from memory. Thus, depending on the algorithm and problem limitations, it can be CPU-bound or memory-bound, meaning that the running time is dominated by one of its components.

Can be fetched ahead, but there is only 50% chance we will get it right on the first layer, then 25% chance on second and so on. We could do 2, 4, 8 and so on fetches, but these would grow exponentially.

IMAGE HERE

If array is large enough—usually around the point where it stops fitting in cache and fetches become significantly slower—the running time of binary search becomes dominated by memory fetches.


So, to sum up: ideally, we'd want some layout that is both blocks, and higher-order blocks to be placed in groups, and also to be capable.

We can overcome this by enumerating and permuting array elements in a more cache-friendly way. The numeration we will use is actually half a millennium old, and chances are you already know it.

## Why Binary Search is Slow

Before jumping to optimized variants, let's briefly discuss the reasons why the textbook binary search is slow in the first place.

Here is the standard way of searching for the first element not less than $x$ in a sorted array of $n$ integers:

```cpp
int lower_bound(int x) {
    int l = 0, r = n - 1;
    while (l < r) {
        int t = (l + r) / 2;
        if (a[t] >= x)
            r = t;
        else
            l = t + 1;
    }
    return a[l];
}
```

Find the middle element of the search range, compare to $x$, cut the range in half. Beautiful in its simplicity.

### Spacial Locality

* First ~10 queries may be cached (frequently accessed: temporal locality)
* Last 3-4 queries may be cached (may be in the same cache line: data locality)
* But that's it. Maybe store elements in a more cache-friendly way?

![](../img/binary-search.png)

### Temporal Locality

When we find lower bound of $x$ in a sorted array by binary searching, the main problem is that its memory accesses pattern is neither temporary nor spatially local. 

For example, element $\lfloor \frac n 2 \rfloor$ is accessed very often (every search) and element $\lfloor \frac n 2 \rfloor + 1$ is not, while they are probably occupying the same cache line. In general, only the first 3-5 reads are temporary local and only the last 3-4 reads are spatially local, and the rest are just random memory accesses.

![](../img/binary-heat.png)

## Eytzinger Layout

**Michaël Eytzinger** is a 16th century Austrian nobleman known for his work on genealogy, particularily for a system for numbering ancestors called *ahnentafel* (German for "ancestor table").

Ancestry mattered a lot back then, but writing down that data was expensive. *Ahnentafel* allows displaying a person's genealogy compactly, without wasting extra space by drawing diagrams.

It lists a person's direct ancestors in a fixed sequence of ascent. First, the person theirself is listed as number 1, and then, recursively, for each person numbered $k$, their father is listed as $2k$ and their mother as $(2k+1)$.

Here is the example for Paul I, the great-grandson of Peter I, the Great:

1. Paul I
2. Peter III (Paul's father)
3. Catherine II (Paul's mother)
4. Charles Frederick (Peter's father, Paul's paternal grandfather)
5. Anna Petrovna (Peter's mother, Paul's paternal grandmother)
6. Christian August (Catherine's father, Paul's maternal grandfather)
7. Johanna Elisabeth (Catherine's mother, Paul's maternal grandmother)

Apart from being compact, it has some nice properties, like that all even-numbered persons are male and all odd-numbered (possibly apart from 1) are female.

One can also find the number of a particular ancestor only knowing the genders of their descendants. For example, Peter the Great's bloodline is Paul I → Peter III → Anna Petrovna → Peter the Great, so his number should be $((1 \times 2) \times 2 + 1) \times 2 = 10$.

**In computer science**, this enumeration has been widely used for implicit (i. e. pointer-free) implementation of heaps, segment trees, and other binary tree structures, where instead of names it stores underlying array items.

This is how this layout will look when applied to binary search:

![](../img/eytzinger.png)

You can immediately see how its temporal locality is better (in fact, theoretically optimal) as the elements closer to the root are closer to the beginning of the array, and thus are more likely to be fetched from cache.

![](../img/eytzinger-search.png)
![](../img/eytzinger-heat.png)

### Construction

Here is a function that constructs Eytzinger array by traversing the original search tree. 

It takes two indexes $i$ and $k$—one in the original array and one in constructed—and recursively goes to two branches until a leaf node is reached, which could simply be checked by asserting $k \leq n$ as Eytzinger array should have same number of items.

```c++
int a[n], b[n + 1]; // <- change name

void eytzinger(int k = 1) {
    static int i = 0; // <- careful running it multiple times
    if (k <= n) {
        eytzinger(2 * k);
        t[k] = _a[i++];
        eytzinger(2 * k + 1);
    }
}
```

Despite being recursive, this is actually a really fast implementation as all memory reads are sequential.

Note that the first element is left unfilled and the whole array is essentially 1-shifted. This will actually turn out to be a huge performance booster.

## Binary search implementation

We can now descend this array using only indices: we just start with $k=1$ and execute $k := 2k$ if we need to go left and $k := 2k + 1$ if we need to go right. We don't even need to store and recalculate binary search boundaries anymore.

The only problem arises when we need to restore the index of the resulting element, as $k$ may end up not pointing to a leaf node. Here is an example of how that can happen:

```python
    array:  1 2 3 4 5 6 7 8
eytzinger:  4 2 5 1 6 3 7 8
1st range:  ---------------  k := 1
2nd range:  -------          k := 2*k      (=2)
3rd range:      ---          k := 2*k + 1  (=5)
4th range:        -          k := 2*k + 1  (=11)
```

Here we query array of $[1, …, 8]$ for the lower bound of $x=4$. We compare it against $4$, $2$ and $5$, and go left-right-right and end up with $k = 11$, which isn't even a valid array index.

Note that, unless the answer is the last element of the array, we compare $x$ against it at some point, and after we learn that it is not less than $x$, we start comparing $x$ against elements to the left, and all these comparisons will evaluate true (i. e. leading to the right). Hence, the solution to restoring the resulting element is to cancel some number of right turns.

This can be done in an elegant way by observing that the right turns are recorded in the binary notation of $k$ as 1-bits, and so we just need to find the number of trailing ones in the binary notation and right-shift $k$ by exactly that amount.

To do this we can invert the number (`~x`) and call "find first set" instruction available on most systems. In GCC, the corresponding builtin is `__builtin_ffs`.

```c++
int lower_bound(int x) {
    int k = 1;
    while (k <= n)
        k = 2 * k + (t[k] < x);
    k >>= __builtin_ffs(~k);
    return t[k];
}
```

![](../img/search-eytzinger.svg)

### Prefetching

We could prefetch not just its 2 children.

```c++
t = (int*) std::aligned_alloc(64, 4 * (n + 1));

int lower_bound(int x) {
    int k = 1;
    while (k <= n) {
        __builtin_prefetch(t + k * B);
        k = 2 * k + (t[k] < x);
    }
    k >>= __builtin_ffs(~k);
    return t[k];
}
```

```c++
__builtin_prefetch(t + k * B * 2);
```

![](../img/search-eytzinger-prefetch.svg)

### Last branch

Let's zoom in.

![](../img/search-eytzinger-small.svg)

```c++
t[0] = -1; // an element that is less than X
iters = std::__lg(n + 1);
```

```c++
int lower_bound(int x) {
    int k = 1;
    for (int i = 0; i < iters; i++)
        k = 2 * k + (t[k] < x);
    int *loc = (k <= n ? t + k : t);
    k = 2 * k + (*loc < x);
    k >>= __builtin_ffs(~k);
    return t[k];
}
```

![](../img/search-eytzinger-branchless.svg)

That was a detour.

## B-Tree Layout

B-trees are basically $(k+1)$-ary trees, meaning that they store $k$ elements in each node and choose between $(k+1)$ possible branches instead of 2.

They are widely used for indexing in databases, especially those that operate on-disk, because if $k$ is big, this allows large sequential memory accesses while reducing the height of the tree.

To perform static binary searches, one can implement a B-tree in an implicit way, i. e. without actually storing any pointers and spending only $O(1)$ additional memory, and $k$ could be made equal to the cache line size so that each node request fetches exactly one cache line.

![](../img/b-tree.png)

Turns out, they have the same rate of growth but sligtly larger compute-tied constant. While the latter is explainable (our while loop only has like 5 instructions; can't outpace that), the former is surprising.

Let's assume that arithmetic costs nothing and do simple cache block analysis:

* The Eytzinger binary search is supposed to be $4$ times faster if compute didn't matter, as it requests them ~4 times faster on average.

* The B-tree makes $\frac{\log_{17} n}{\log_2 n} = \frac{\log n}{\log 17} \frac{\log 2}{\log n} = \frac{\log 2}{\log 17} \approx 0.245$ memory access per each request of binary search, i. e. it requests ~4 times less cache lines to fetch

This explains why they have roughly the same slope.

Note that this method, while being great for single-threaded world, is unlikely to make its way into database and heavy multi-threaded applications, because it sacrifices bandwidth to achieve low latency.

[Part 2](https://algorithmica.org/en/b-tree) explores efficient implementation of implicit static B-trees in bandwidth-constrained environment.

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

## Acknowledgements

The first half of the article is loosely based on "[Array Layouts for Comparison-Based Searching](https://arxiv.org/pdf/1509.05053.pdf)" by Paul-Virak Khuong and Pat Morin. It is 46 pages long, and discusses the scalar binary searches in more details, so check it out if you're interested in other approaches.

This [StackOverflow answer](https://stackoverflow.com/questions/20616605/using-simd-avx-sse-for-tree-traversal) by Cory Nelson is where I took the permuted SIMD routine.

The more you think about the name. "S-tree" and "S+ tree" respectively. There is a an obscure data structures in computer vision. We even have more claim to it than Boer had on B-tree: it is succinct, simd, my name, my surname.

<!--

I stole some pictures from blogs and I can't find the originals.

-->
