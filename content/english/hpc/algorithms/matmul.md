---
title: Matrix Multiplication
weight: 20
draft: true
---

"[Anatomy of High-Performance Matrix Multiplication](https://www.cs.utexas.edu/~flame/pubs/GotoTOMS_revision.pdf)" by Kazushige Goto and Robert van de Geijn.

Inspired by "[Programming Parallel Computers](http://ppc.cs.aalto.fi/ch2/)" course.

For reasons that will later become aparent, we only use sizes that are multiples of $48$. 1920

Cache associativity strikes again. This is also an issue, but we will not address it for now.

GCC 13.

3.5s for 1025 ad 12s for 1024.

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

$$
C_{ij} = \sum_{i=1}^{n} A_{ik} \cdot B_{kj}
$$

Implement the definition of what we need to do, but using arrays instead of matrices:

```c++
void matmul(const float *a, const float *b, float *c, int n) {
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                c[i * n + j] += a[i * n + k] * b[k * n + j];
}
```

Transpose:

```c++
void matmul(const float *a, const float *_b, float *c, int n) {
    float *b = new float[n * n];

    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            b[i * n + j] = _b[j * n + i];
    
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                c[i * n + j] += a[i * n + k] * b[j * n + k]; // notice indices
}
```

```c++
void matmul(const float *a, const float *_b, float * __restrict__ c, int n) {
    // ...
}
```

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

![](../img/mm-vectorized-barplot.svg)

![](../img/mm-vectorized-plot.svg)

## Theoretical Performance

$$
\underbrace{4}_{CPUs} \cdot \underbrace{8}_{SIMD} \cdot \underbrace{2}_{1/thr} \cdot \underbrace{3.6 \cdot 10^9}_{cycles/sec} = 230.4 \; GFLOPS \;\; (2.3 \cdot 10^{11})
$$

RAM bandwidth is lower than that


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

![](../img/mm-noalloc.svg)

![](../img/mm-blas.svg)

Which is fine, considering that this is not the only thing that CPUs are made for.

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
