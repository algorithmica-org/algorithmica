---
title: Sums and Other Reductions
weight: 3
---

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
