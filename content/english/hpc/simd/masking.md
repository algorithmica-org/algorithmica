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

```c++
for (int i = 0; i < N; i++)
    a[i] = rand() % 100;

for (int i = 0; i < N; i++)
    s += (a[i] < 50 ? a[i] : 0);
```

```c++
const reg c = _mm256_set1_epi32(49);
const reg z = _mm256_setzero_si256();
reg s = _mm256_setzero_si256();

for (int i = 0; i < N; i += 8) {
    reg x = _mm256_load_si256( (reg*) &a[i] );
    reg mask = _mm256_cmpgt_epi32(x, c);
    x = _mm256_blendv_epi8(x, z, mask);
    s = _mm256_add_epi32(s, x);
}
```

```c++
const reg c = _mm256_set1_epi32(50);
reg s = _mm256_setzero_si256();

for (int i = 0; i < N; i += 8) {
    reg x = _mm256_load_si256( (reg*) &a[i] );
    reg mask = _mm256_cmpgt_epi32(c, x);
    x = _mm256_and_si256(x, mask);
    s = _mm256_add_epi32(s, x);
}
```

```c++
vec *v = (vec*) a;
vec s = {};

for (int i = 0; i < N / 8; i++)
    s += (v[i] < 50 ? v[i] : 0);
```


```nasm
vpcmpeqd        ymm0, ymm1, YMMWORD PTR a[0+rdx*4]
vptest  ymm0, ymm0
je      .L2
```

```nasm
vpcmpeqd        ymm0, ymm1, YMMWORD PTR a[0+rdx*4]
vmovmskps       eax, ymm0
test    eax, eax
je      .L9
```

All at around 13 GFLOPS, and the compiler can handle vectorization by itself. Let's move on to more complex examples that can't be auto-vectorized.

### Searching

4.4:

```c++
int find(int x) {
    for (int i = 0; i < N; i++)
        if (a[i] == x)
            return i;
    return -1;
}
```

19.63, ~5 times faster:

```c++
int find(int needle) {
    reg x = _mm256_set1_epi32(needle);

    for (int i = 0; i < N; i += 8) {
        reg y = _mm256_load_si256( (reg*) &a[i] );
        reg m = _mm256_cmpeq_epi32(x, y);
        int mask = _mm256_movemask_ps((__m256) m);
        if (mask != 0)
            return i + __builtin_ctz(mask);
    }

    return -1;
}
```

A slightly faster alternative:

```c++
int find(int needle) {
    reg x = _mm256_set1_epi32(needle);

    for (int i = 0; i < N; i += 8) {
        reg y = _mm256_load_si256( (reg*) &a[i] );
        reg m = _mm256_cmpeq_epi32(x, y);
        if (!_mm256_testz_si256(m, m)) {
            int mask = _mm256_movemask_ps((__m256) m);
            return i + __builtin_ctz(mask);
        }
    }

    return -1;
}
```

### Counting Values

15 GFLOPS:

```c++
int count(int needle) {
    int cnt = 0;
    for (int i = 0; i < N; i++)
        cnt += (a[i] == needle);
    return cnt;
}
```

Also 15 GFLOPS:

```c++
const reg ones = _mm256_set1_epi32(1);

int count(int needle) {
    reg x = _mm256_set1_epi32(needle);
    reg s = _mm256_setzero_si256();

    for (int i = 0; i < N; i += 8) {
        reg y = _mm256_load_si256( (reg*) &a[i] );
        reg m = _mm256_cmpeq_epi32(x, y);
        m = _mm256_and_si256(m, ones);
        s = _mm256_add_epi32(s, m);
    }

    return hsum(s);
}

```

The trick that the compiler couldn't find is to notice that all ones is minus one. So we can use it as the negative count, achieving 22 GFLOPS:

```c++
int count(int needle) {
    reg x = _mm256_set1_epi32(needle);
    reg s1 = _mm256_setzero_si256();
    reg s2 = _mm256_setzero_si256();

    for (int i = 0; i < N; i += 16) {
        reg y1 = _mm256_load_si256( (reg*) &a[i] );
        reg y2 = _mm256_load_si256( (reg*) &a[i + 8] );
        reg m1 = _mm256_cmpeq_epi32(x, y1);
        reg m2 = _mm256_cmpeq_epi32(x, y2);
        s1 = _mm256_add_epi32(s1, m1);
        s2 = _mm256_add_epi32(s2, m2);
    }

    s1 = _mm256_add_epi32(s1, s2);

    return -hsum(s1);
}
```
