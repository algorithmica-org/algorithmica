---
title: In-Register Shuffles
weight: 6
---

[Masking](../masking) lets you apply operations to only a subset of vector elements. It is a very effective and frequently used data manipulation technique, but in many cases, you need to perform more advanced operations that involve permuting values inside a vector register instead of just blending them with other vectors.

The problem is that adding a separate element-shuffling instruction for each possible use case in hardware is unfeasible. What we can do though is to add just one general permutation instruction that takes the indices of a permutation and produce these indices using precomputed lookup tables.

This general idea is perhaps too abstract, so let's jump straight to the examples.

### Shuffles and Popcount

*Population count*, also known as the *Hamming weight*, is the count of `1` bits in a binary string.

It is a frequently used operation, so there is a separate instruction on x86 that computes the population count of a word:

```c++
const int N = (1<<12);
int a[N];

int popcnt() {
    int res = 0;
    for (int i = 0; i < N; i++)
        res += __builtin_popcount(a[i]);
    return res;
}
```

It also supports 64-bit integers, improving the total throughput twofold:

```c++
int popcnt_ll() {
    long long *b = (long long*) a;
    int res = 0;
    for (int i = 0; i < N / 2; i++)
        res += __builtin_popcountl(b[i]);
    return res;
}
```

The only two instructions required are load-fused popcount and addition. They both have a high throughput, so the code processes about $8+8=16$ bytes per cycle as it is limited by the decode width of 4 on this CPU.

These instructions were added to x86 CPUs around 2008 with SSE4. Let's temporarily go back in time before vectorization even became a thing and try to implement popcount by other means.

The naive way is to go through the binary string bit by bit: 

```c++
__attribute__ (( optimize("no-tree-vectorize") ))
int popcnt() {
    int res = 0;
    for (int i = 0; i < N; i++)
        for (int l = 0; l < 32; l++)
            res += (a[i] >> l & 1);
    return res;
}
```

As anticipated, it works just slightly faster than ⅛-th of a byte per cycle — at around 0.2.

We can try to process in bytes instead of individual bits by [precomputing](/hpc/compilation/precalc) a small 256-element *lookup table* that contains the population counts of individual bytes and then query it while iterating over raw bytes of the array:

```c++
struct Precalc {
    alignas(64) char counts[256];

    constexpr Precalc() : counts{} {
        for (int m = 0; m < 256; m++)
            for (int i = 0; i < 8; i++)
                counts[m] += (m >> i & 1);
    }
};

constexpr Precalc P;

int popcnt() {
    auto b = (unsigned char*) a; // careful: plain "char" is signed
    int res = 0;
    for (int i = 0; i < 4 * N; i++)
        res += P.counts[b[i]];
    return res;
}
```

It now processes around 2 bytes per cycles, rising to ~2.7 if we switch to 16-bit words (`unsigned short`).

This solution is still very slow compared the `popcnt` instruction, but now it can be vectorized. Instead of trying to speed it up through [gather](../moving#non-contiguous-load) instructions, we will go for another approach: make the lookup table small enough to fit inside a register and then use a special [pshufb](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=pshuf&techs=AVX,AVX2&expand=6331) instruction to look up its values in parallel.

The original `pshufb` introduced in 128-bit SSE3 takes two registers: the lookup table containing 16 byte values and a vector of 16 4-bit indices (0 to 15), specifying which bytes to pick for each position. In 256-bit AVX2, instead of a 32-byte lookup table with awkward 5-bit indices, we have an instruction that independently the same shuffling operation over two 128-bit lanes.

So, for our use case, we create a 16-byte lookup table with population counts for each nibble (half-byte), repeated twice:

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
```

Now, to compute the population count of a vector, we split each of its bytes into the lower and higher nibbles and then use this lookup table to retrieve their counts. The only thing left is to carefully sum them up:

```c++
const reg low_mask = _mm256_set1_epi8(0x0f);

int popcnt() {
    int k = 0;

    reg t = _mm256_setzero_si256();

    for (; k + 15 < N; k += 15) {
        reg s = _mm256_setzero_si256();
        
        for (int i = 0; i < 15; i += 8) {
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

This code processes around 30 bytes per cycle. Theoretically, the inner loop could do 32, but we have to stop it every 15 iterations because the 8-bit counters can overflow. 

The `pshufb` instruction is so instrumental in some SIMD algorithms that [Wojciech Muła](http://0x80.pl/) — the guy who came up with this algorithm — took it as his [Twitter handle](https://twitter.com/pshufb). You can calculate population counts even faster: check out his [github repository](https://github.com/WojciechMula/sse-popcount) with different vectorized popcount implementations and his [recent paper](https://arxiv.org/pdf/1611.07612.pdf) for a detailed explanation of the state-of-the-art.

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
