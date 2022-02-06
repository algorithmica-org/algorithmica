---
title: In-Register Shuffles
weight: 6
---

[Masking](../masking) lets you apply operations to only a subset of vector elements. It is a very effective and frequently used data manipulation technique, but in many cases, you need to perform more advanced operations that involve permuting values inside a vector register instead of just blending them with other vectors.

The problem is that adding a separate element-shuffling instruction for each possible use case in hardware is unfeasible. What we can do though is to add just one general permutation instruction that takes the indices of a permutation and produce these indices using precomputed lookup tables.

This general idea is perhaps too abstract, so let's jump straight to examples.

### Permutations and Lookup Tables

One very important data processing primitive is the `filter`. It takes an array as input and writes out only the elements that satisfy a given predicate. In a single-threaded scalar case, it is trivially implemented by maintaining a counter that is incremented on each write:

```c++
int a[N], b[N];

int filter() {
    int k = 0;

    for (int i = 0; i < N; i++)
        if (a[i] < P)
            b[k++] = a[i];

    return k;
}
```

To vectorize it, we will use the `_mm256_permutevar8x32_epi32` intrinsic. It takes a vector of values and a vector of indices, and selects them correspondingly. It doesn't really permute but selects the values.

The general idea:
- to calculate the predicate (perform the comparison and get the mask),
- use `movemask` to get a scalar 8-bit mask,
- then use a lookup use this instruction
- permute so that values are in the beginning
- write to the buffer only the element that satisfy the predicate (and maybe some garbage later)
- move pointer (by the popcnt of movemask)

6-7x faster:

```c++
struct Precalc {
    alignas(64) int permutation[256][8];

    constexpr Precalc() : permutation{} {
        for (int m = 0; m < 256; m++) {
            int k = 0;
            for (int i = 0; i < 8; i++)
                if (m >> i & 1)
                    permutation[m][k++] = i;
        }
    }
};

constexpr Precalc T;
```

You can [permute](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=permute&techs=AVX,AVX2&expand=6331,5160) data inside a register almost arbitrarily.

```c++
const reg p = _mm256_set1_epi32(P);

int filter() {
    int k = 0;

    for (int i = 0; i < N; i += 8) {
        reg x = _mm256_load_si256( (reg*) &a[i] );
        
        reg m = _mm256_cmpgt_epi32(p, x);
        int mask = _mm256_movemask_ps((__m256) m);
        reg permutation = _mm256_load_si256( (reg*) &T.permutation[mask] );
        
        x = _mm256_permutevar8x32_epi32(x, permutation);
        _mm256_storeu_si256((reg*) &b[k], x);
        
        k += __builtin_popcount(mask);
    }

    return k;
}
```

It also doesn't depend on the value of `P`:

![](../img/filter.svg)

AVX512 has similar "scatter" instructions that write data non-sequentially, using either indices or [a mask](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=compress&expand=4754,4479&techs=AVX_512). You can very efficiently "filter" an array this way using a predicate.

### Shuffles and Popcount

We can create tiny lookup tables with [pshufb](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=pshuf&techs=AVX,AVX2&expand=6331) instruction. This is useful when you have some logic that isn't implemented in SSE, and this operation is so instrumental in some algorithms that [Wojciech Muła](http://0x80.pl/) — the guy who came up with a half of the algorithms described in this chapter — took it as his [Twitter handle](https://twitter.com/pshufb).

2 GFLOPS:

```c++
int popcnt() {
    int res = 0;
    for (int i = 0; i < N; i++)
        res += __builtin_popcount(a[i]);
    return res;
}
```

4 GFLOPS:

```c++
int popcnt() {
    long long *b = (long long*) a;
    int res = 0;
    for (int i = 0; i < N / 2; i++)
        res += __builtin_popcountl(b[i]);
    return res;
}
```

0.49 GFLOPS (0.66 when switching to 16-bit and unsigned short).

```c++
struct Precalc {
    alignas(64) char counts[256];

    constexpr Precalc() : counts{} {
        for (int i = 0; i < 256; i++)
            counts[i] = __builtin_popcount(i);
    }
};

constexpr Precalc P;

int popcnt() {
    auto b = (unsigned char*) a; // char is signed by default
    int res = 0;
    for (int i = 0; i < 4 * N; i++)
        res += P.counts[b[i]];
    return res;
}
```

7.5-8 GFLOPS:

```c++
const reg lookup = _mm256_setr_epi8(
    /* 0 */ 0, /* 1 */ 1, /* 2 */ 1, /* 3 */ 2,
    /* 4 */ 1, /* 5 */ 2, /* 6 */ 2, /* 7 */ 3,
    /* 8 */ 1, /* 9 */ 2, /* a */ 2, /* b */ 3,
    /* c */ 2, /* d */ 3, /* e */ 3, /* f */ 4,

    /* 0 */ 0, /* 1 */ 1, /* 2 */ 1, /* 3 */ 2,
    /* 4 */ 1, /* 5 */ 2, /* 6 */ 2, /* 7 */ 3,
    /* 8 */ 1, /* 9 */ 2, /* a */ 2, /* b */ 3,
    /* c */ 2, /* d */ 3, /* e */ 3, /* f */ 4
);

const reg low_mask = _mm256_set1_epi8(0x0f);

const int block_size = (255 / 8) * 8;

int popcnt() {
    int k = 0;

    reg t = _mm256_setzero_si256();

    for (; k + block_size < N; k += block_size) {
        reg s = _mm256_setzero_si256();
        
        for (int i = 0; i < block_size; i += 8) {
            reg x = _mm256_load_si256( (reg*) &a[k + i] );
            
            reg l = _mm256_and_si256(x, low_mask);
            reg h = _mm256_and_si256(_mm256_srli_epi16(x, 4), low_mask);

            reg pl = _mm256_shuffle_epi8(lookup, l);
            reg ph = _mm256_shuffle_epi8(lookup, h);

            s = _mm256_add_epi8(s, pl);
            s = _mm256_add_epi8(s, ph);
        }

        t = _mm256_add_epi64(t, _mm256_sad_epu8(s, _mm256_setzero_si256()));
    }

    int res = hsum(t);

    while (k < N)
        res += __builtin_popcount(a[k++]);

    return res;
}
```

Another way is through gather, but that is too slow.

### Acknowledgements

Check out [Wojciech Muła's github repository](https://github.com/WojciechMula/sse-popcount) with different vectorized popcount implementations and his [latest paper](https://arxiv.org/pdf/1611.07612.pdf) for the detailed explanation of state-of-the-art.
