---
title: Prefix Sum with SIMD
weight: 8
draft: true
---

We design a 2.5x faster algorithm per the prefix sum problem, also known as cumulative sum, inclusive scan, or simply scan.

$$
\begin{aligned}
b_0 &= a_0
\\ b_1 &= a_0 + a_1
\\ b_2 &= a_0 + a_1 + a_2
\\ &\ldots
\end{aligned}
$$

In other words, the $k$-th element of the output is the sum of the first $k$ elements of the input.

`{1, 2, 3, 4}` is `{1, 3, 6, 10}`

### Baseline

For our scalar baseline:

```c++
void prefix(int *a, int n) {
    for (int i = 1; i < n; i++)
        a[i] += a[i - 1];
}
```

The compiler, of course, doesn't do extra reads and uses a separate variable:

```nasm
loop:
    add     edx, DWORD PTR [rax]
    mov     DWORD PTR [rax-4], edx
    add     rax, 4
    cmp     rax, rcx
    jne     loop
```

When unrolling happens, there are only two instructions: fused load-add and writing the results back.

`std::partial_sum` does the same. Less than 1 value per cycle because both reads and writes are needed.

### Vectorization

The main idea is to split the array in small blocks, calculate the prefix sums on these blocks

```c++
typedef __m128i v4i;

v4i prefix(v4i x) {
    x = _mm_add_epi32(x, _mm_slli_si128(x, 4));
    x = _mm_add_epi32(x, _mm_slli_si128(x, 8));
    return s;
}
```

Essentially, 

This 128-bit lane separation is typical for AVX.

`{1, 2, 3, 4, 5, 6, 7, 8}` is `{1, 3, 6, 10, 5, 11, 18, 26}`

```c++
void prefix(int *p) {
    v8i x = _mm256_load_si256((v8i*) p);
    x = _mm256_add_epi32(x, _mm256_slli_si256(x, 4));
    x = _mm256_add_epi32(x, _mm256_slli_si256(x, 8));
    _mm256_store_si256((v8i*) p, x);
}
```

Not managing to come up with a more characteristic name, we are going to call it `update`:

```c++
v4i update(int *p, v4i s) {
    v4i d = broadcast(&p[3]);
    v4i x = _mm_load_si128((v4i*) p);
    x = _mm_add_epi32(s, x);
    _mm_store_si128((v4i*) p, x);
    return _mm_add_epi32(s, d);
}
```

```c++
void prefix(int *a, int n) {
    for (int i = 0; i < n; i += 8)
        prefix(&a[i]);
    
    v4i s = _mm_setzero_si128();
    
    for (int i = 4; i < n; i += 4)
        s = update(&a[i], s);
}
```

![](../img/prefix-simd.svg)

We have a problem with memory.

only update: 5.8
only prefix: 8.1

### Blocking

Write it in the same style as we did `update`:

```c++
const int B = 4096; // adjust block size to your L1 cache size

v4i local_prefix(int *a, v4i s) {
    for (int i = 0; i < B; i += 8)
        prefix(&a[i]);
    
    for (int i = 0; i < B; i += 4)
        s = update(&a[i], s);

    return s;
}

void prefix(int *a, int n) {
    v4i s = _mm_setzero_si128();
    for (int i = 0; i < n; i += B)
        s = local_prefix(a + i, s);
}
```

(You have to make sure that $N$ is a multiple of $B$, but we are going to ignore that for now.)

![](../img/prefix-blocked.svg)

### Continuous Loads

The cache system is sitting idle when we do a second pass.

One solution is to explicitly add [software prefetching](/hpc/cpu-cache/prefetching):

```c++
v4i update(int *p, v4i s) {
    __builtin_prefetch(p + B); // <-- prefetch next block's data
    // ...
    return s;
}
```

![](../img/prefix-prefetch.svg)

Interleaving:

```c++
const int B = 64;

void prefix(int *a, int n) {
    v4i s = _mm_setzero_si128();

    for (int i = 0; i < B; i += 8)
        prefix(&a[i]);

    for (int i = B; i < n; i += 8) {
        prefix(&a[i]);
        s = update(&a[i - B], s);
        s = update(&a[i - B + 4], s);
    }

    for (int i = n - B; i < n; i += 4)
        s = update(&a[i], s);
}
```

![](../img/prefix-interleaved.svg)

You can also combine it with prefetching, which improves performance even more.

![](../img/prefix-interleaved-prefetch.svg)

It is sort of "meh". There are ways to do it with permutations, but it would kill the performance of the prefix stage.

The speedup may be higher for lower-precision data as the scalar code can execute at most one iteration per cycle anyway

### Other Relevant Work

There is this professor at CMU named [Guy Blelloch](https://www.cs.cmu.edu/~blelloch/) who [advocated](https://www.cs.cmu.edu/~blelloch/papers/sc90.pdf) back in the 90s where the idea of  for vector computers having

Luckily, parallel. You can read [paper](http://www.adms-conf.org/2020-camera-ready/ADMS20_05.pdf) (AVX-512 which has — sort of — ) and [this StackOverflow discussion](https://stackoverflow.com/questions/10587598/simd-prefix-sum-on-intel-cpu) for a more general overview.

Most of what I described is already known. To the best of my knowledge, the contributions of this article is the interleaving technique, which is only responsible for a ~20% performance increase.
