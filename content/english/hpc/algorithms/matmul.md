---
title: Matrix Multiplication
weight: 20
draft: true
---

"[Anatomy of High-Performance Matrix Multiplication](https://www.cs.utexas.edu/~flame/pubs/GotoTOMS_revision.pdf)" by Kazushige Goto and Robert van de Geijn.

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

![](../img/mm-vectorized-barplot.svg)

![](../img/mm-vectorized-plot.svg)

![](../img/mm-kernel-barplot.svg)

![](../img/mm-kernel-plot.svg)

![](../img/mm-blocked-plot.svg)

![](../img/mm-blocked-barplot.svg)

![](../img/mm-noalloc.svg)

![](../img/mm-blas.svg)

Which is fine, considering that this is not the only thing that CPUs are made for.

---

## Case Study: Distance Product

(We are going to speedrun "[Programming Parallel Computers](http://ppc.cs.aalto.fi/ch2/)" course)

Given a matrix $D$, we need to calculate its "min-plus matrix multiplication" defined as:

$(D \circ D)_{ij} = \min_k(D_{ik} + D_{kj})$

----

Graph interpretation:
find shortest paths of length 2 between all vertices in a fully-connected weighted graph

![](https://i.imgur.com/Zf4G7qj.png)

----

A cool thing about distance product is that if if we iterate the process and calculate:

$D_2 = D \circ D, \;\;
D_4 = D_2 \circ D_2, \;\;
D_8 = D_4 \circ D_4, \;\;
\ldots$

Then we can find all-pairs shortest distances in $O(\log n)$ steps

(but recall that there are [more direct ways](https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm) to solve it) <!-- .element: class="fragment" data-fragment-index="1" -->

---

## V0: Baseline

Implement the definition of what we need to do, but using arrays instead of matrices:

```cpp
const float infty = std::numeric_limits<float>::infinity();

void step(float* r, const float* d, int n) {
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            float v = infty;
            for (int k = 0; k < n; ++k) {
                float x = d[n*i + k];
                float y = d[n*k + j];
                float z = x + y;
                v = std::min(v, z);
            }
            r[n*i + j] = v;
        }
    }
}
```

Compile with `g++ -O3 -march=native -std=c++17`

On our Intel Core i5-6500 ("Skylake," 4 cores, 3.6 GHz) with $n=4000$ it runs for 99s,
which amounts to ~1.3B useful floating point operations per second

---

## Theoretical Performance

$$
\underbrace{4}_{CPUs} \cdot \underbrace{8}_{SIMD} \cdot \underbrace{2}_{1/thr} \cdot \underbrace{3.6 \cdot 10^9}_{cycles/sec} = 230.4 \; GFLOPS \;\; (2.3 \cdot 10^{11})
$$

RAM bandwidth: 34.1 GB/s (or ~10 bytes per cycle)
<!-- .element: class="fragment" data-fragment-index="1" -->

---

## OpenMP

* We have 4 cores, so why don't we use them?
* There are low-level ways of creating threads, but they involve a lot of code
* We will use a high-level interface called OpenMP
* (We will talk about multithreading in much more detail on the next lecture)

![](https://www.researchgate.net/profile/Mario_Storti/publication/231168223/figure/fig2/AS:393334787985424@1470789729707/The-master-thread-creates-a-team-of-parallel-threads.png =400x)

----

## Multithreading Made Easy

All you need to know for now is the `#pragma omp parallel for` directive

```cpp
#pragma omp parallel for
for (int i = 0; i < 10; ++i) {
    do_stuff(i);
}
```

It splits iterations of a loop among multiple threads

There are many ways to control scheduling,
but we'll just leave defaults because our use case is simple
<!-- .element: class="fragment" data-fragment-index="1" -->


----

## Warning: Data Races

This only works when all iterations can safely be executed simultaneously
It's not always easy to determine, but for now following rules of thumb are enough:

* There must not be any shared data element that is read by X and written by Y
* There must not be any shared data element that is written by X and written by Y

E. g. sum can't be parallelized this way, as threads would modify a shared variable
<!-- .element: class="fragment" data-fragment-index="1" -->

---

## Parallel Baseline

OpenMP is included in compilers: just add `-fopenmp` flag and that's it

```cpp
void step(float* r, const float* d, int n) {
    #pragma omp parallel for
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            float v = infty;
            for (int k = 0; k < n; ++k) {
                float x = d[n*i + k];
                float y = d[n*k + j];
                float z = x + y;
                v = std::min(v, z);
            }
            r[n*i + j] = v;
        }
    }
}
```

Runs ~4x times faster, as it should

---

## Memory Bottleneck

![](https://i.imgur.com/z4d6aez.png =450x)

(It is slower on macOS because of smaller page sizes)

----

## Virtual Memory

![](https://www.cs.uic.edu/~jbell/CourseNotes/OperatingSystems/images/Chapter9/9_01_VirtualMemoryLarger.jpg =500x)

---

## V1: Linear Reading

Just transpose it, as we did with matrices

```cpp
void step(float* r, const float* d, int n) {
    std::vector<float> t(n*n);
    #pragma omp parallel for
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            t[n*j + i] = d[n*i + j];
        }
    }

    #pragma omp parallel for
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            float v = std::numeric_limits<float>::infinity();
            for (int k = 0; k < n; ++k) {
                float x = d[n*i + k];
                float y = t[n*j + k];
                float z = x + y;
                v = std::min(v, z);
            }
            r[n*i + j] = v;
        }
    }
}
```

----

![](https://i.imgur.com/UwxcEG7.png =600x)

----

![](https://i.imgur.com/2ySfr0V.png =600x)

---

## V2: Instruction-Level Parallelism

We can apply the same trick as we did with array sum earlier, so that instead of:

```cpp
v = min(v, z0);
v = min(v, z1);
v = min(v, z2);
v = min(v, z3);
v = min(v, z4);
```

We use a few registers and compute minimum simultaneously utilizing ILP:

```cpp
v0 = min(v0, z0);
v1 = min(v1, z1);
v0 = min(v0, z2);
v1 = min(v1, z3);
v0 = min(v0, z4);
...
v = min(v0, v1);
```

----

![](https://i.imgur.com/ihMC6z2.png)

Our memory layout looks like this now

----

```cpp
void step(float* r, const float* d_, int n) {
    constexpr int nb = 4;
    int na = (n + nb - 1) / nb;
    int nab = na*nb;

    // input data, padded
    std::vector<float> d(n*nab, infty);
    // input data, transposed, padded
    std::vector<float> t(n*nab, infty);

    #pragma omp parallel for
    for (int j = 0; j < n; ++j) {
        for (int i = 0; i < n; ++i) {
            d[nab*j + i] = d_[n*j + i];
            t[nab*j + i] = d_[n*i + j];
        }
    }

    #pragma omp parallel for
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            // vv[0] = result for k = 0, 4, 8, ...
            // vv[1] = result for k = 1, 5, 9, ...
            // vv[2] = result for k = 2, 6, 10, ...
            // vv[3] = result for k = 3, 7, 11, ...
            float vv[nb];
            for (int kb = 0; kb < nb; ++kb) {
                vv[kb] = infty;
            }
            for (int ka = 0; ka < na; ++ka) {
                for (int kb = 0; kb < nb; ++kb) {
                    float x = d[nab*i + ka * nb + kb];
                    float y = t[nab*j + ka * nb + kb];
                    float z = x + y;
                    vv[kb] = std::min(vv[kb], z);
                }
            }
            // v = result for k = 0, 1, 2, ...
            float v = infty;
            for (int kb = 0; kb < nb; ++kb) {
                v = std::min(vv[kb], v);
            }
            r[n*i + j] = v;
        }
    }
}
```

----

![](https://i.imgur.com/5uHVRL4.png =600x)

---

## V3: Vectorization

![](https://i.imgur.com/EG0WjHl.png =400x)

----

```cpp
static inline float8_t min8(float8_t x, float8_t y) {
    return x < y ? x : y;
}

void step(float* r, const float* d_, int n) {
    // elements per vector
    constexpr int nb = 8;
    // vectors per input row
    int na = (n + nb - 1) / nb;

    // input data, padded, converted to vectors
    float8_t* vd = float8_alloc(n*na);
    // input data, transposed, padded, converted to vectors
    float8_t* vt = float8_alloc(n*na);

    #pragma omp parallel for
    for (int j = 0; j < n; ++j) {
        for (int ka = 0; ka < na; ++ka) {
            for (int kb = 0; kb < nb; ++kb) {
                int i = ka * nb + kb;
                vd[na*j + ka][kb] = i < n ? d_[n*j + i] : infty;
                vt[na*j + ka][kb] = i < n ? d_[n*i + j] : infty;
            }
        }
    }

    #pragma omp parallel for
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            float8_t vv = f8infty;
            for (int ka = 0; ka < na; ++ka) {
                float8_t x = vd[na*i + ka];
                float8_t y = vt[na*j + ka];
                float8_t z = x + y;
                vv = min8(vv, z);
            }
            r[n*i + j] = hmin8(vv);
        }
    }

    std::free(vt);
    std::free(vd);
}
```

----

![](https://i.imgur.com/R3OvLKO.png =600x)

---

## V4: Register Reuse

* At this point we are actually bottlenecked by memory
* It turns out that calculating one $r_{ij}$ at a time is not optimal
* We can reuse data that we read into registers to update other fields

----

![](https://i.imgur.com/ljvD0ba.png =400x)

----

```cpp
for (int ka = 0; ka < na; ++ka) {
    float8_t y0 = vt[na*(jc * nd + 0) + ka];
    float8_t y1 = vt[na*(jc * nd + 1) + ka];
    float8_t y2 = vt[na*(jc * nd + 2) + ka];
    float8_t x0 = vd[na*(ic * nd + 0) + ka];
    float8_t x1 = vd[na*(ic * nd + 1) + ka];
    float8_t x2 = vd[na*(ic * nd + 2) + ka];
    vv[0][0] = min8(vv[0][0], x0 + y0);
    vv[0][1] = min8(vv[0][1], x0 + y1);
    vv[0][2] = min8(vv[0][2], x0 + y2);
    vv[1][0] = min8(vv[1][0], x1 + y0);
    vv[1][1] = min8(vv[1][1], x1 + y1);
    vv[1][2] = min8(vv[1][2], x1 + y2);
    vv[2][0] = min8(vv[2][0], x2 + y0);
    vv[2][1] = min8(vv[2][1], x2 + y1);
    vv[2][2] = min8(vv[2][2], x2 + y2);
}
```

Ugly, but worth it

----

![](https://i.imgur.com/GZvIt8J.png =600x)

---

## V5: More Register Reuse

![](https://i.imgur.com/amUznoQ.png =400x)

----

![](https://i.imgur.com/24nBJ1Y.png =600x)

---

## V6: Software Prefetching

![](https://i.imgur.com/zwqa1ZS.png =600x)

---

## V7: Temporal Cache Locality

![](https://i.imgur.com/29vTLKJ.png)

----

### Z-Curve

![](https://i.imgur.com/0optLZ3.png)

----

![](https://i.imgur.com/U3GaO5b.png)

---

## Summary

* Deal with memory problems first (make sure data fits L3 cache)
* SIMD can get you ~10x speedup
* ILP can get you 2-3x speedup
* Multi-core parallelism can get you $NUM_CORES speedup
 (and it can be just one `#pragma omp parallel for` away)
