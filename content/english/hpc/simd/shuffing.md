---
title: In-Register Shuffles
weight: 6
---

Masking is the most widely used technique for data manipulation, but there are many other handy SIMD features that we will later use in this chapter:

### Permutations and Lookup Tables

AVX512 has similar "scatter" instructions that write data non-sequentially, using either indices or [a mask](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=compress&expand=4754,4479&techs=AVX_512). You can very efficiently "filter" an array this way using a predicate.

You can [permute](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=permute&techs=AVX,AVX2&expand=6331,5160) data inside a register almost arbitrarily.

```c++
int filter() {
    int k = 0;

    for (int i = 0; i < N; i++)
        if (a[i] < P)
            b[k++] = a[i];

    return k;
}
```

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

![](../img/filter.svg)

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

https://github.com/WojciechMula/sse-popcount

https://arxiv.org/pdf/1611.07612.pdf for the state-of-the-art.
