---
title: Masking and Blending
weight: 4
---

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

<!-- some example of maskmov -->
