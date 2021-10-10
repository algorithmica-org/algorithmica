---
title: (Auto-)Vectorization
weight: 2
---

Most often, SIMD is used for "embarrassingly parallel" computations: the ones where all you do is apply some elementwise function to all elements of an array and write it back somewhere else. In this setting, you don't even need to know how SIMD works: the compiler is perfectly capable of optimizing such loops by itself. All you need to know is that such optimization exists and yields a 5-10x speedup.

But most computations are not like that, and even the loops that seem straightforward to vectorize are often not optimized because of some tricky technical nuances. In this section, we will discuss how to assist the compiler in vectorization and walk through some more complicated patterns of using SIMD.

## Reductions

We will start with the example of calculating the sum an array:

```c++
int sum_naive(int *a, int n) {
    int s = 0;
    for (int i = 0; i < n; i++)
        s += a[i];
    return s;
}
```

The naive approach is not so straightforward to vectorize, because the state of the loop (sum $s$ on the current prefix) depends on the previous iteration. The way to overcome this is to split a single scalar accumulator $s$ into 8 separate ones, so that $s_i$ would contain the sum of every 8th element of the original array, shifted by $i$:

$$
s_i = \sum_{j=0}^{n / 8} a_{8 \cdot j + i }
$$

If we store these 8 accumulators in a single 256-bit vector, we can update them all at once by adding consecutive 8-element segments of the array. Armed with [the GCC vector extension](../x86-simd) syntax, this is straightforward:

```c++
int sum_simd(v8si *a, int n) {
    //       ^ you can just cast a pointer normally, like with any other pointer type
    v8si s = {0};

    for (int i = 0; i < n / 8; i++)
        s += a[i];
    
    int res = 0;
    
    // sum 8 accumulators into one
    for (int i = 0; i < 8; i++)
        res += s[i];

    // add the remainder of a
    for (int i = n / 8 * 8; i < n; i++)
        res += a[i];
        
    return res;
}
```

This is how compilers actually vectorize array sums and other reduction. Surprisingly, this is not the fastest way to do it, and we will come back to this problem in the last chapter to show why.

### Horizontal Summation

The last part, where we sum up the 8 accumulators stored in a vector register into a single scalar to get the total sum, is called "horizontal summation". Although extracting and adding every scalar one by one only takes a constant number of cycles, it can be computed slightly faster using a [special instruction](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#techs=AVX,AVX2&text=_mm256_hadd_epi32&expand=2941) that adds together pairs of adjacent elements in a register.

![](../img/hsum.png)

Since it is a very specific operation, it can only be expressed using SIMD intrinsics, although the compiler probably emits roughly the same procedure anyway:

```c++
int hsum(__m256i x) {
    __m128i l = _mm256_extracti128_si256(x, 0);
    __m128i h = _mm256_extracti128_si256(x, 1);
    l = _mm_add_epi32(l, h);
    l = _mm_hadd_epi32(l, l);
    return _mm_extract_epi32(l, 0) + _mm_extract_epi32(l, 1);
}
```

There are similar techniques for computing "horizontal minimum" and some other reductions.

## Memory Alignment

Operations of reading and writing the contents of a SIMD register into memory have two versions each: `load` / `loadu` and `store` / `storeu`. The letter "u" here stands for "unaligned". The difference is that the former ones only work correctly when the read / written block fits inside a single cache line (and crash otherwise), while the latter work either way, but with a slight performance penalty if the block crosses a cache line.

Sometimes, especially when the "inner" operation is very lightweight, the performance difference becomes significant (at least because you need to fetch two cache lines instead of one). As an extreme example, this way of adding two arrays together:

```c++
for (int i = 3; i + 7 < n; i += 8) {
    __m256i x = _mm256_loadu_si256((__m256i*) &a[i]);
    __m256i y = _mm256_loadu_si256((__m256i*) &b[i]);
    __m256i z = _mm256_add_epi32(x, y);
    _mm256_storeu_si256((__m256i*) &c[i], z);
}
```

…is ~30% slower than its aligned version:

```c++
for (int i = 0; i < n; i += 8) {
    __m256i x = _mm256_load_si256((__m256i*) &a[i]);
    __m256i y = _mm256_load_si256((__m256i*) &b[i]);
    __m256i z = _mm256_add_epi32(x, y);
    _mm256_store_si256((__m256i*) &c[i], z);
}
```

In the first version, assuming that arrays `a`, `b` and `c` are all 64-byte *aligned* (the addresses of their first elements are divisible by 64, and so they start at the beginning of a cache line), roughly half of reads and writes will be "bad" because they cross a cache line boundary.

### Data Alignment

By default, when you allocate an array, the only guarantee about its alignment you get is that none of its elements are split by a cache line. For an array of `int`, this means that it gets the alignment of 4 bytes (`sizeof int`), which lets you load exactly one cache line when reading any element.

For our purposes, we want to guarantee that any (256-bit = 32-byte) SIMD block will not be split, so we need to specify the alignment of 32 bytes. For static arrays, we can do so with the `alignas` specifier:

```c++
alignas(32) float a[n];

for (int i = 0; i < n; i += 8) {
    __m256 x = _mm256_load_ps(&a[i]);
    // ...
}
```

For allocating an array dynamically, we can use `std::aligned_alloc` which takes the alignment value and the size of array in bytes, and returns a pointer to the allocated memory (just like `new` does), which should be explicitly deleted when no longer used.

On most modern architectures, the `loadu` / `storeu` intrinsics should be equally as fast as `load` / `store` given that in both cases the blocks only intersect one cache line. The advantage of the latter is that they can act as free assertions that all reads and writes are aligned. It is worth noting that the GCC vector extensions always assume aligned memory reads and writes. Memory alignment issues is also one of the reasons why compilers can't always autovectorize efficiently.

## Data Manipulation

If you took some time to study [the reference](https://software.intel.com/sites/landingpage/IntrinsicsGuide), you may have noticed that there are essentially two major groups of vector operations:

1. Instructions that perform some elementwise operation (`+`, `*`, `<`, `acos`, etc.).
2. Instructions that load, store, mask, shuffle and generally move data around.

While using the elementwise instructions is easy, the largest challenge with SIMD is getting the data in vector registers in the first place, with low enough overhead so that the whole endeavor is worthwhile.

### Masking

SIMD has no easy way to do branching, because the control flow should be the same for all elements in a vector. To overcome this limitation, we can "mask" operations that should only be performed on a subset of elements, in a way similar to how a [conditional move](/hpc/analyzing-performance/assembly) is executed.

Consider the following problem: for some reason, we need to raise $10^8$ random integers to some random powers.

```c++
const int n = 1e8;
alignas(32) unsigned bases[n], results[n], powers[n];
```

In SSE/AVX, [doing modular reduction](/hpc/arithmetic/integer) is even more complicated than in the scalar case (e. g. SSE has no integer division in the first place), so we will perform all operations modulo $2^{32}$ by naturally overflowing an `unsigned int`.

We'd normally do it by exponentiation by squaring:

```c++
void binpow_simple() {
    for (int i = 0; i < n; i++) {
        unsigned a = bases[i], p = powers[i];

        unsigned res = 1;
        while (p > 0) {
            if (p & 1)
                res = (res * a);
            a = (a * a);
            p >>= 1;
        }

        results[i] = res;
    }
}
```

This code runs in 9.47 seconds.

To vectorize it, we can first split the arrays `a` and `p` into groups of 8 elements, and then run exponentiation by squaring on them for 32 iterations (the maximum for any 32-bit power), masking the elements that need to be squared:

```c++
typedef __m256i reg;

void binpow_simd() {
    const reg ones = _mm256_set_epi32(1, 1, 1, 1, 1, 1, 1, 1);
    for (int i = 0; i < n; i += 8) {
        reg a = _mm256_load_si256((__m256i*) &bases[i]);
        reg p = _mm256_load_si256((__m256i*) &powers[i]);
        reg res = ones;

        // in fact, there will not be a cycle here:
        // the compiler should unroll it in 32 separate blocks of operations
        for (int l = 0; l < 32; l++) {
            // instead of explicit branching, calculate a "multiplier" for every element:
            // it is either 1 or a, depending on the lowest bit of p
            
            // masks of elements that should be multiplied by a:
            reg mask = _mm256_cmpeq_epi32(_mm256_and_si256(p, ones), ones);
            // now we blend a vector of ones and a vector of a using this mask:
            reg mul = _mm256_blendv_epi8(ones, a, mask);
            // res *= mul:
            res = _mm256_mullo_epi32(res, mul);
            // a *= a:
            a = _mm256_mullo_epi32(a, a);
            // p >>= 1:
            p = _mm256_srli_epi32(p, 1);
        }

        _mm256_store_si256((__m256i*) &results[i], res);
    }
}
```

This implementation now works in 0.7 seconds, or 13.5 times faster, and there is still ample room for improvement.

### Advanced Data Twiddling

Masking is the most widely used technique for data manipulation, but there are many other handy SIMD features that we will later use in this chapter:

- You can [broadcast](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#expand=6331,5160,588&techs=AVX,AVX2&text=broadcast) a single value to a vector from a register or a memory location.
- You can [permute](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=permute&techs=AVX,AVX2&expand=6331,5160) data inside a register almost arbitrarily.
- We can create tiny lookup tables with [pshufb](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=pshuf&techs=AVX,AVX2&expand=6331) instruction. This is useful when you have some logic that isn't implemented in SSE, and this operation is so instrumental in some algorithms that [Wojciech Muła](http://0x80.pl/) — the guy who came up with a half of the algorithms described in this chapter — took it as his [Twitter handle](https://twitter.com/pshufb)
- Since AVX2, you can use "gather" instructions that load data non-sequentially using arbitrary array indices. These don't work 8 times faster though and are usually limited by memory rather than CPU, but they are still helpful for stuff like sparse linear algebra.
- AVX512 has similar "scatter" instructions that write data non-sequentially, using either indices or [a mask](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=compress&expand=4754,4479&techs=AVX_512). You can very efficiently "filter" an array this way using a predicate.

The last two, gather and scatter, turn SIMD into proper parallel programming model, where most operations can be executed independently in terms of their memory locations. This is a huge deal: many AVX512-specific algorithms have been developed recently owning to these new instructions, and not just having twice as many SIMD lanes.

## Assisting Autovectorization

Of course, the preferred way of using SIMD is by the means of autovectorization. Whenever you can, you should always stick with the scalar code for its simplicity and maintainability. But, [as in many other cases](/hpc/analyzing-performance/compilation), compiler often needs some additional input from the programmer, who may know a little bit more about the problem.

Consider the "a+b" example:

```c++
void sum(int a[], int b[], int c[], int n) {
    for (int i = 0; i < n; i++)
        c[i] = a[i] + b[i];
}
```

This function can't be replaced with the vectorized variant automatically. Why?

First, vectorization here is not always technically correct. Assuming that `a[]` and `c[]` intersect in a way that their beginnings differ by a single position — because who knows, maybe the programmer wanted to calculate the Fibonacci sequence through a convolution this way. In this case, the data in the SIMD blocks will intersect, and the observed behavior will differ from the one in the scalar case.

Second, we don't know anything about the alignment of these arrays, and we can lose some performance here by using unaligned instructions.

On high (`-O3`) levels of optimization, when the compiler suspects that the function may be used for large cycles, it generates two implementation variants — a SIMDized and a "safe" one — and inserts runtime checks to choose between the two.

To avoid these runtime checks, we can tell compiler that we are sure that nothing will break. One way to do this is using the `__restrict__` keyword:

```cpp
void add(int * __restrict__ a, const int * __restrict__ b, int n) {
    for (int i = 0; i < n; i++)
        a[i] += b[i];
}
```

The other, specific to SIMD, is the "ignore vector dependencies" pragma, which is the way to tell compiler that we are sure there are no dependencies between the loop iterations:

```c++
#pragma GCC ivdep
for (int i = 0; i < n; i++)
    // ...
```

There are [many other ways](https://software.intel.com/sites/default/files/m/4/8/8/2/a/31848-CompilerAutovectorizationGuide.pdf) of hinting compiler what we meant exactly, but in especially complex cases — when inside the loop there are a lot of branches or some functions are called — it is easier to go down to the intrinsics level and write it yourself.
