---
title: Argmin with SIMD
weight: 7
draft: true
---

We create an array of *random* integers.

```c++
const int n = (1 << 16);
alignas(32) int a[n];

for (int i = 0; i < n; i++)
    a[i] = rand();
```

```c++
int argmin(int *a, int n) {
    int k = 0;

    for (int i = 0; i < n; i++)
        if (a[i] < a[k])
            k = i;
    
    return k;
}
```

```c++
int argmin(int *a, int n) {
    int k = std::min_element(a, a + n) - a;
    return k;
}
```

The compiler couldn't pierce through STL's abstractions, which isn't surprising at this point.

```c++
int argmin(int *a, int n) {
    int k = 0;

    for (int i = 0; i < n; i++)
        if (a[i] < a[k]) [[unlikely]]
            k = i;
    
    return k;
}
```

[Optimized machine layout](/hpc/architecture/layout).

```c++
int argmin(int *a, int n) {
    int k = 0;

    for (int i = 0; i < n; i++)
        if (__builtin_expect_with_probability(a[i] < a[k], true, 0.5))
            k = i;
    
    return k;
}
```

```c++
typedef int vec __attribute__ (( vector_size(32) ));

int argmin(int *a, int n) {
    vec *v = (vec*) a;
    
    vec min = INT_MAX + vec{};
    vec idx;

    vec cur = {0, 1, 2, 3, 4, 5, 6, 7};

    for (int i = 0; i < n / 8; i++) {
        vec mask = (v[i] < min);
        idx = (mask ? cur : idx);
        min = (mask ? v[i] : min);
        cur += B;
    }
    
    int k = 0, m = min[0];

    for (int i = 1; i < 8; i++)
        if (min[i] < m)
            m = min[k = i];

    return idx[k];
}
```

```c++
typedef __m256i reg;

int argmin(int *a, int n) {
    int m = INT_MAX, k = 0;
    vec p, t;
    t = p = m + vec{};

    for (int i = 0; i < n / B; i++) {
        t = min(t, v[i]);
        int mask = _mm256_movemask_epi8((__m256i) (p == t));
        if (mask != -1) { [[unlikely]]
            for (int j = B * i; j < B * i + 2 * B; j++)
                if (a[j] < m)
                    m = a[k = j];
            t = p = m + vec{};
        }
    }
    
    return k;
}
```

```c++
vec min(vec x, vec y) {
    return (x < y ? x : y);
}

int argmin() {
    vec *v = (vec*) a;
    
    int m = INT_MAX, k = 0;
    vec t0, t1, p;
    t0 = t1 = p = m + vec{};

    for (int i = 0; i < n / B; i += 2) {
        t0 = min(t0, v[i]);
        t1 = min(t1, v[i + 1]);
        vec t = min(t0, t1);
        int mask = _mm256_movemask_epi8((__m256i) (p == t));
        if (mask != -1) { [[unlikely]]
            for (int j = B * i; j < B * i + 2 * B; j++)
                if (a[j] < m)
                    m = a[k = j];
            t0 = t1 = p = m + vec{};
        }
    }
    
    return k;
}
```

```
std 0.28 0.28
simple 1.58 1.94
cmov 1.43 1.93
hint 2.26 1.49
index 4.36 4.36
simdmin-single 9.26 0.53
simdmin 14.22 1.37
simdmin-testz 13.51 1.41
```