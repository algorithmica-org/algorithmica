---
title: Loading and Writing Data
aliases: [/hpc/simd/vectorization]
weight: 2
---

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

### Register Aliasing

MMX was originally used the integer (64-bit mantissa) part of a 80-bit float.


