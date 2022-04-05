---
title: Matrix Multiplication
weight: 20
draft: true
---

<!--
baseline 13.58622 0.5209607970428861
hugepages 16.749895 0.42256312651512146
transposed 12.377302 0.5718441708863531
autovec 3.117215 2.2705806304666187
vectorized 3.075742 2.301196914435606
kernel 2.24264 3.1560517960974566
blocked 0.461477 15.33746643928083
noalloc 0.408031 17.346446716058338
nomove 0.303826 23.295860130469414
blas 0.27489790320396423 25.747333528217077
-->

In this case study, we will design and implement several algorithms for matrix multiplication. We start with the naive "for-for-for" algorithm and incrementally improve it, eventually developing an implementation that is 50 times faster and matches the performance of BLAS libraries while being under 40 lines of C.

We compile our implementations with GCC 13 and run them on Zen 2 clocked at 2GHz.

## Baseline

The result of multiplying an $l \times n$ matrix $A$ by an $n \times m$ matrix $B$ is an $l \times m$ matrix $C$ calculated as:

$$
C_{ij} = \sum_{k=1}^{n} A_{ik} \cdot B_{kj}
$$

For simplicity, we will only consider *square* matrices, where $l = m = n$.

To implement matrix multiplication, we can just transfer this definition into code — but instead of two-dimensional arrays (aka matrices), we will be using one-dimensional arrays, to be explicit about memory addressing:

```c++
void matmul(const float *a, const float *b, float *c, int n) {
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                c[i * n + j] += a[i * n + k] * b[k * n + j];
}
```

For reasons that will become apparent later, we only use matrix sizes that are multiples of $48$ for benchmarking, but the implementations are still correct for all other sizes. We also use [32-bit floats](/hpc/arithmetic/ieee-754) specifically, although it can be [generalized](#generalizations) to other types and operations.

Compiled with `g++ -O3 -march=native -funroll-loops`, the naive approach multiplies two matrices of size $n = 1920$ in ~16.7 seconds. That is approximately $\frac{1920^3}{16.7 \times 10^9} \approx 0.42$ useful operations per nanosecond (GFLOPS), or roughly 5 CPU cycles per multiplication.

## Transposition

In general, when you optimize an algorithm that processes large quantities of data — and $1920^2 \times 3 \times 4 \approx 42$ MB clearly is a large quantity as it can't fit into any of the [CPU caches](/hpc/cpu-cache) — you should always start with memory before optimizing arithmetic, as it is much more likely to be the bottleneck.

Note that the field $C_{ij}$ can be viewed as the dot product of row $i$ in matrix $A$ and column $j$ in matrix $B$. As we are incrementing the `k` variable in the inner loop above, we are reading the matrix `a` sequentially, but we are jumping over $n$ elements as we iterate over a column of `b`, which is [not as fast](/hpc/cpu-cache/aos-soa).

One [well-known optimization](/hpc/external-memory/oblivious/#matrix-multiplication) that mitigates this problem is to either store matrix $B$ in *column-major* order or to *transpose* it before the matrix multiplication — spending $O(n^2)$ additional operations, but ensuring sequential reads in the hot loop:

<!--

![](../img/column-major.jpg)

-->

```c++
void matmul(const float *a, const float *_b, float *c, int n) {
    float *b = new float[n * n];

    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            b[i * n + j] = _b[j * n + i];
    
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                c[i * n + j] += a[i * n + k] * b[j * n + k]; // <- note the indices
}
```

This code runs in ~12.4s, or about 30% faster. As we will see in a bit, there are more important benefits to transposing it than just the sequential memory reads.

## Vectorization

/hpc/compilation/contracts/#memory-aliasing

/hpc/simd/auto-vectorization/

```c++
void matmul(const float *a, const float *_b, float * __restrict__ c, int n) {
    // ...
}
```

![](../img/mm-vectorized-barplot.svg)

```c++
const int B = 8; // number of elements in a vector
const int vecsize = B * sizeof(float); // size of a vector in bytes
typedef float vector __attribute__ (( vector_size(vecsize) ));

vector* alloc(int n) {
    vector* ptr = (vector*) std::aligned_alloc(vecsize, vecsize * n);
    memset(ptr, 0, vecsize * n);
    return ptr;
}

float hsum(vector s) {
    float res = 0;
    for (int i = 0; i < B; i++)
        res += s[i];
    return res;
}

void matmul(const float *_a, const float *_b, float *c, int n) {
    int nB = (n + B - 1) / B;

    vector *a = alloc(n * nB);
    vector *b = alloc(n * nB);

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            a[i * nB + j / 8][j % 8] = _a[i * n + j];
            b[i * nB + j / 8][j % 8] = _b[j * n + i]; // <- still transposed
        }
    }

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            vector s = {0};
            for (int k = 0; k < nB; k++)
                s += a[i * nB + k] * b[j * nB + k];
            c[i * n + j] = hsum(s);
        }
    }
}
```

![](../img/mm-vectorized-plot.svg)

[memory bandwidth](/hpc/cpu-cache/bandwidth/) is not the problem.

[Cache associativity](/hpc/cpu-cache/associativity/) strikes again. This is also an issue, but we will not address it for now.

$1920 = 2^7 \times 3 \times 5$, so it is divisible by a large power of two.

Slightly slower than.

3.5s for 1025 ad 12s for 1024.

However, now we *really* hit the memory limit.

## Register reuse

This CPU importantly supports the [FMA3](https://en.wikipedia.org/wiki/FMA_instruction_set) SIMD extension that we will utilize in later implementations.

RAM bandwidth is lower than that

The latency of FMA is 5 cycles, while its reciprocal throughput is ½. 

```c++
void kernel(float *a, vector *b, vector *c, int x, int y, int l, int r, int n) {
    vector t[6][2]{};

    for (int k = l; k < r; k++) {
        for (int i = 0; i < 6; i++) {
            vector alpha = vector{} + a[(x + i) * n + k];
            for (int j = 0; j < 2; j++)
                t[i][j] += alpha * b[(k * n + y) / 8 + j];
        }
    }

    for (int i = 0; i < 6; i++)
        for (int j = 0; j < 2; j++)
            c[((x + i) * n + y) / 8 + j] += t[i][j];
}
```

```c++
void matmul(const float *_a, const float *_b, float *_c, int n) {
    int nx = (n + 5) / 6 * 6;
    int ny = (n + 15) / 16 * 16;
    
    float *a = alloc(nx * ny);
    float *b = alloc(nx * ny);
    float *c = alloc(nx * ny);

    for (int i = 0; i < n; i++) {
        memcpy(&a[i * ny], &_a[i * n], 4 * n);
        memcpy(&b[i * ny], &_b[i * n], 4 * n);
    }

    for (int x = 0; x < nx; x += 6)
        for (int y = 0; y < ny; y += 16)
            kernel(a, (vector*) b, (vector*) c, x, y, 0, n, ny);

    for (int i = 0; i < n; i++)
        memcpy(&_c[i * n], &c[i * ny], 4 * n);
    
    std::free(a);
    std::free(b);
    std::free(c);
}
```

![](../img/mm-kernel-barplot.svg)

![](../img/mm-kernel-plot.svg)

```c++
const int s3 = 64;
const int s2 = 120;
const int s1 = 240;

for (int i3 = 0; i3 < ny; i3 += s3)
    // now we are working with b[:][i3:i3+s3]
    for (int i2 = 0; i2 < nx; i2 += s2)
        // now we are working with a[i2:i2+s2][:]
        for (int i1 = 0; i1 < ny; i1 += s1)
            // now we are working with b[i1:i1+s1][i3:i3+s3]
            // this equates to updating c[i2:i2+s2][i3:i3+s3]
            // with [l:r] = [i1:i1+s1]
            for (int x = i2; x < std::min(i2 + s2, nx); x += 6)
                for (int y = i3; y < std::min(i3 + s3, ny); y += 16)
                    kernel(a, (vector*) b, (vector*) c, x, y, i1, std::min(i1 + s1, n), ny);
```

![](../img/mm-blocked-plot.svg)

![](../img/mm-blocked-barplot.svg)

Avoid moving anything:

![](../img/mm-noalloc.svg)

$$
\underbrace{4}_{CPUs} \cdot \underbrace{8}_{SIMD} \cdot \underbrace{2}_{1/thr} \cdot \underbrace{3.6 \cdot 10^9}_{cycles/sec} = 230.4 \; GFLOPS \;\; (2.3 \cdot 10^{11})
$$

![](../img/mm-blas.svg)

We hit about 95.

Which is fine, considering that this is not the only thing that CPUs are made for.

```c++
for (int i3 = 0; i3 < n; i3 += s3)
    for (int i2 = 0; i2 < n; i2 += s2)
        for (int i1 = 0; i1 < n; i1 += s1)
            for (int x = i2; x < i2 + s2; x += 6)
                for (int y = i3; y < i3 + s3; y += 16)
                    for (int k = i1; k < i1 + s1; k++)
                        for (int i = 0; i < 6; i++)
                            for (int j = 0; j < 2; j++)
                                c[x * n / 8 + i * n / 8 + y / 8 + j]
                                += (vector{} + a[x * n + i * n + k])
                                   * b[n / 8 * k + y / 8 + j];
```

### Generalizations

Given a matrix $D$, we need to calculate its "min-plus matrix multiplication" defined as:

$(D \circ D)_{ij} = \min_k(D_{ik} + D_{kj})$

Graph interpretation: find shortest paths of length 2 between all vertices in a fully-connected weighted graph

A cool thing about distance product is that if if we iterate the process and calculate:

$$
D_2 = D \circ D \\
D_4 = D_2 \circ D_2 \\
D_8 = D_4 \circ D_4 \\
\ldots
$$

Then we can find all-pairs shortest distances in $O(\log n)$ steps

(but recall that there are [more direct ways](https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm) to solve it)

Which is an exercise.

Strassen algorithm is only useful for large matrices.

https://arxiv.org/pdf/1605.01078.pdf

[cache-oblivious](/hpc/external-memory/oblivious/#matrix-multiplication) algorithms

## Acknowledgements

"[Anatomy of High-Performance Matrix Multiplication](https://www.cs.utexas.edu/~flame/pubs/GotoTOMS_revision.pdf)" by Kazushige Goto and Robert van de Geijn.

Inspired by "[Programming Parallel Computers](http://ppc.cs.aalto.fi/ch2/)" course.
