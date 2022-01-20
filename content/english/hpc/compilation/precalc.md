---
title: Compile-Time Computation
weight: 8
draft: true
---

### Precalculation

A compiler can compute constants on its own, but it doesn't *have to*.

```c++
const int b = 4, B = (1 << b);

// is it tight enough?
constexpr int round(int k) {
    return k / B * B; // (k & ~(B - 1));
}

constexpr int height(int m) {
    return (m == 0 ? 0 : height(m / B) + 1);
}

constexpr int offset(int h) {
    int res = 0;
    int m = N;
    while (h--) {
        res += round(m) + B;
        m /= B;
    }
    return res;
}

constexpr int h = height(N);
alignas(64) int t[offset(h)];
//int t[N * B / (B - 1)]; // +1?

struct Meta {
    alignas(64) int mask[B][B];

    constexpr Meta() : mask{} {
        for (int k = 0; k < B; k++)
            for (int i = 0; i < B; i++)
                mask[k][i] = (i > k ? -1 : 0);
    }
};

constexpr Meta T;
```

### Code Generation

There are plenty of languages that support computing *data* during compile-time, but none can produce efficient code at all times.

One huge example is generating lexers and parsers: which is usually done in.

For example, CUDA and OpenCL are mostly C, and have no support for metaprogramming.

At some point (and perhaps to this day), these languages had no way to unroll loops, so people would write a [jinja template](https://jinja.palletsprojects.com/en/3.0.x/), call the thing from Python, and then compile.

It is not uncommon to use a templating engine to generate code. For example, CUDA (a GPU programming language) has no loop unrolling
