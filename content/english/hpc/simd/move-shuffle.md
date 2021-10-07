---
title: Moving and Shuffling Data
weight: 3
draft: true
---

If you took some time to study the reference, you may have noticed that there are essentially two major groups of vector operations:

1. Instructions that perform some elementwise operation (`+`, `*`, `<`, `acos`, etc.).
2. Instructions that load, store, mask, shuffle and generally move data around.

While using the elementwise instructions is easy, the largest challenge with SIMD is getting the data in vector registers in the first place, preferrably with low enough overhead that makes the whole endeavor worthwhile.

## Loading Data

Intrinsics for reading and writing vector data have two versions: `load` / `loadu` and `store` / `storeu`. The letter "u" here stands for "unaligned". The difference is that the former ones only work correctly when the read / written block fits inside a single cache line (and crash otherwise), while the latter work regardless, albeit with a slight performance penalty if the block crosses a cache line.

As an extreme example, assuming that arrays `a`, `b` and `c` are all 32-bytes alligned, this code:

```c++
for (int i = 3; i + 7 < n; i += 8) {
    __m256i x = _mm256_loadu_si256((__m256i*) &a[i]);
    __m256i y = _mm256_loadu_si256((__m256i*) &b[i]);
    __m256i z = _mm256_add_epi32(x, y);
    _mm256_storeu_si256((__m256i*) &c[i], z);
}
```

...will be 30% slower than its aligned version:

```c++
for (int i = 0; i < n; i += 8) {
    __m256i x = _mm256_load_si256((__m256i*) &a[i]);
    __m256i y = _mm256_load_si256((__m256i*) &b[i]);
    __m256i z = _mm256_add_epi32(x, y);
    _mm256_store_si256((__m256i*) &c[i], z);
}
```

In the first version, roughly half of reads and writes will be "bad" because they cross a cache line boundary.

### Data Alignment

TODO: move it to memory chapter

`std::aligned_alloc`, that takes an alignment value and the size of array.


```c++
alignas(32) float a[n];

for (int i = 0; i < n; i += 8) {
    __m256 x = _mm256_load_ps(&a[i]);
    // ...
}
```

### Gather

In AVX2, you can also read non-continuous data using gather instructions.

These don't work 8 times faster though and are usually limited by memory rather than CPU, but they are still helpful with stuff like sparse linear algebra.

### Nontemporal Memory

These don't occupy cache line and work faster.

`stream`

## Masking

## Swizzling

## Lookup Tables



### AVX-512

In this book, we focus on AVX2, which should be available on 95% or desktop and server computers.

Algorithms specifically for AVX-512 are frequently published in blogs and research papers, so you would need to know the differences anyway. Here is a brief list of what AVX-512 extensions can do:

- Scattered writes
- "Compressed" writes