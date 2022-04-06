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

Compiled with `g++ -O3 -march=native -ffast-math -funroll-loops`, the naive approach multiplies two matrices of size $n = 1920 = 48 \times 40$ in ~16.7 seconds. That is approximately $\frac{1920^3}{16.7 \times 10^9} \approx 0.42$ useful operations per nanosecond (GFLOPS), or roughly 5 CPU cycles per multiplication.

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

Now that we are just sequentially reading the elements of `a` and `b`, multiplying them, and adding the result to an accumulator variable, we can use [SIMD](/hpc/simd/) instructions to speed it up like [any other reduction](/hpc/simd/reduction/).

We can use [GCC vector types](/hpc/simd/intrinsics/#gcc-vector-extensions) to implement it:

```c++
// a vector of 256 / 32 = 8 floats
typedef float vec __attribute__ (( vector_size(32) ));

// helper function that allocates n vectors and initializes them with zeros
vec* alloc(int n) {
    vec* ptr = (vec*) std::aligned_alloc(32, 32 * n);
    memset(ptr, 0, 32 * n);
    return ptr;
}

void matmul(const float *_a, const float *_b, float *c, int n) {
    // first, we need to align rows and pad them with zeros
    int nB = (n + 7) / 8; // number of 8-element vectors in a row (rounded up)

    vec *a = alloc(n * nB);
    vec *b = alloc(n * nB);

    // move both matrices
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            a[i * nB + j / 8][j % 8] = _a[i * n + j];
            b[i * nB + j / 8][j % 8] = _b[j * n + i]; // <- b is still transposed
        }
    }

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            vec s{}; // initialize the accumulator with zeros

            // vertical summation
            for (int k = 0; k < nB; k++)
                s += a[i * nB + k] * b[j * nB + k];
            
            // horizontal summation
            for (int k = 0; k < 8; k++)
                c[i * n + j] += s[k];
        }
    }

    std::free(a);
    std::free(b);
}
```

The performance for $n = 1920$ is now around 2.3 GFLOPS — or another ~4 times higher.

![](../img/mm-vectorized-barplot.svg)

This optimization looks neither too complex or specific to matrix multiplication. Why can't the compiler simply [auto-vectorizate](/hpc/simd/auto-vectorization/) the inner loop? It actually can — the only thing preventing that is the possibility that `c` overlaps with either `a` or `b`. The only thing that you need to do is to guarantee that `c` is not [aliased](/hpc/compilation/contracts/#memory-aliasing) with anything by adding the `__restrict__` keyword to it:

<!-- (the compiler already knows that reading `a` and `b` is safe in any order because they are marked as `const`): -->

```c++
void matmul(const float *a, const float *_b, float * __restrict__ c, int n) {
    // ...
}
```

Both manually and auto-vectorized implementations perform roughly the same.

The performance is bottlenecked by using a single variable. We could use multiple variables similar to other reductions, but we will solve it later anyway.

## Memory efficiency

Now, what is interesting is that the implementation efficiency depends on the problem size. 

At first, the performance (in terms of useful operations per second) increases, as the overhead of the loop management and horizontal reduction decreases. Then, at around $n=256$, it starts smoothly decreasing as the matrices stop fitting into the [cache](/hpc/cpu-cache/) ($2 \times 256^2 \times 4 = 512$ KB is the size of the L2 cache), and the performance becomes bottlenecked by the [memory bandwidth](/hpc/cpu-cache/bandwidth/).

![](../img/mm-vectorized-plot.svg)

It is also interesting that the naive implementation is mostly on par with the non-vectorized transposed version — and actually slightly better because of the transpose itself — for all but few data points, where the performance deteriorates. This is because of [cache associativity](/hpc/cpu-cache/associativity/): when $n$ is divisible by a large power of two, we are fetching addresses of `b` that all likely map to the same cache line, reducing the effective cache size. This explains the 30% performance dip for $n = 1920 = 2^7 \times 3 \times 5$, and you can see an even more noticeable one for $1536 = 2^9 \times 3$: it is roughly 3 times slower than for $n=1535$.

One may think that there would be at least some general performance gain from full sequential reads since we are fetching fewer cache lines, but this is not the case: fetching the first column of `b` is painful, but the next 15 columns will actually be in the same cache lines as the first one, so they will be cached — unless the matrix is so large that it can't even fit `n * cache_line_size` bytes into the cache, which is not the case for all practical problem sizes.

So, counterintuitively, transposing the matrix doesn't help the memory bandwidth — and in the naive implementation, we are not really bottlenecked by it anyway. But for our vectorize implementation, we certainly are, so let's tackle it.

## Register reuse

Any two cells of A and B are used to update some cell of C.

To compute the cell $C[i][j]$, we need to compute the dot product of $A[i][:]$ and $B[:][j]$ (we are using the Python notation here to select rows and columns), which requires fetching $2n$ elements, even when $B$ is stored in column-major order.

What if we were to compute $C[i:i+2][j:j+2]$, a $2 \times 2$ submatrix of $C$? We would need $A[i:i+2][:]$ and $B[:][j:j+2]$, which is $4n$ elements in total: that is $\frac{2n / 1}{4n / 4} = 2$ times better in terms of I/O efficiency.

To actually avoid reading more data, we need to read these $2+2$ rows and columns in parallel and update all $2 \times 2$ cells at once using all possible combinations of products.

Here is a proof of concept:

```c++
void update_2x2(int x, int y) {
    int c00 = c[x][y],
        c01 = c[x][y + 1],
        c10 = c[x + 1][y],
        c11 = c[x + 1][y + 1];

    for (int k = 0; k < n; k++) {
        int a0 = a[x][k];
        int a1 = a[x + 1][k];

        int b0 = b[k][y];
        int b1 = b[k][y + 1];

        c00 += a0 * b0;
        c01 += a0 * b1;
        c10 += a1 * b0;
        c11 += a1 * b1;
    }

    c[x][y]         = c00;
    c[x][y + 1]     = c01;
    c[x + 1][y]     = c10;
    c[x + 1][y + 1] = c11;
}
```

It also boosts instruction-level parallelism (we don't have to wait between iterations to update the loop state) and saves some cycles from executing the read instructions.

Of course, although better in terms of I/O, this $2 \times 2$ update would not beat our vectorized implementation, so we are not going to try this version in particular and instead will scale the idea right away.

## Designing the kernel

We follow this approach and design a general kernel that updates a $h \times w$ submatrix of C using columns from $l$ to $r$ of $A$ and rows from $l$ to $r$ of $B$ (i. e. not a full computation, but only a partial update — it will be clear why later). We have several considerations:

- In general, if we are updating an $h \times w$ submatrix, we will be fetching $2 \cdot n \cdot (h + w)$ elements to update $h \cdot w$ elements. We want that ratio of $\frac{h \cdot w}{2 \cdot n \cdot (h + w)}$ to be as high as possible, which is achieved with large square-ish submatrices.
- We want to use the [FMA](https://en.wikipedia.org/wiki/FMA_instruction_set) ("fused multiply-add") instructions that are available on all modern x86 architectures. As you can guess from the name, they perform a vector `c += a * b` operation in one go, which is the core of our computation.
- We want to be able to exploit [instruction-level parallelism](/hpc/pipelining/) to achieve better utilizaiton of this instruction. On Zen 2, the `fma` instruction has the latency of 5 and the throughput of 2, meaning that we need to concurrently execute at least $5 \times 2 = 10$ of them to fully saturate its execution ports.
- We only have $16$ logical vector registers that we can use as accumulators, and we want to avoid register spill.

For these reasons, we settle on a $6 \times 16$ kernel. We process $96$ elements at once, which can be stored in $6 \times 2 = 12$ vector registers (we need some more to store temporary values). We [broadcast](/hpc/simd/moving/#broadcast) an element of A, and then use it to update the first row ($8 + 8$ elements). Then we load the one below it, and so on. When we have updated the last row, we move to the next $6$ elements to the right.

The final implementation is simpler than it sounds:

```c++
// update 6x16 submatrix C[x:x+6][y:y+16]
// using A[x:x+6][l:r] and B[l:r][y:y+16]
void kernel(float *a, vec *b, vec *c, int x, int y, int l, int r, int n) {
    vec t[6][2]{}; // will be stored in ymm registers

    for (int k = l; k < r; k++) {
        for (int i = 0; i < 6; i++) {
            vec alpha = vec{} + a[(x + i) * n + k];  // broadcast
            for (int j = 0; j < 2; j++)
                t[i][j] += alpha * b[(k * n + y) / 8 + j]; // fused multiply-add
        }
    }

    for (int i = 0; i < 6; i++)
        for (int j = 0; j < 2; j++)
            c[((x + i) * n + y) / 8 + j] += t[i][j];
}
```

We need `t` so that the compiler stores these elements in vector registers. We could just update the final destinations, but unfortunately, the compiler re-writes them back to memory, causing a huge slowdown — and wrapping everything in `__restrict__` keywords doesn't help.

The rest of the implementaiton is straightforward. Similar to the previous vectorized implementation, we just allocate aligned arrays and call the kernel instead of the innermost loop:

```c++
void matmul(const float *_a, const float *_b, float *_c, int n) {
    // to avoid implementing partials,
    // we pad height to nearest 6 and width to 16
    
    int nx = (n + 5) / 6 * 6;
    int ny = (n + 15) / 16 * 16;
    
    float *a = alloc(nx * ny);
    float *b = alloc(nx * ny);
    float *c = alloc(nx * ny);

    for (int i = 0; i < n; i++) {
        memcpy(&a[i * ny], &_a[i * n], 4 * n);
        memcpy(&b[i * ny], &_b[i * n], 4 * n); // we don't need to transpose b this time
    }

    for (int x = 0; x < nx; x += 6)
        for (int y = 0; y < ny; y += 16)
            kernel(a, (vec*) b, (vec*) c, x, y, 0, n, ny);

    for (int i = 0; i < n; i++)
        memcpy(&_c[i * n], &c[i * ny], 4 * n);
    
    std::free(a);
    std::free(b);
    std::free(c);
}
```

This improves the performance by another ~40%:

![](../img/mm-kernel-barplot.svg)

The speedup is much better (2-3x) on smaller arrays, indicating that there is still a bandwidth problem:

![](../img/mm-kernel-plot.svg)

If you've read the section on [cache-oblivious algorithms](/hpc/external-memory/oblivious/), you know that one universal solution to these types of things is to split matrices in four parts, do eight recursive block matrix multiplications until the matrix fits into cache, and carefully combine the results together. We will follow a different, simpler approach.

## Blocking

Alternative to divide-and-conquer is *cache blocking*: selecting a subset of data and processing it, and then going to the next block. Sometimes blocking is hierarchical: we first select a block of data that fits into the L3 cache, then we split it into blocks that fit into the L2 cache, and so on.

It is less trivial to do for matrices than for arrays, but the trick is like this:

- Let's select a subset of B that fits into the L3 cache (say, a subset of its columns).
- Now, let's select a submatrix of A that fits into the L2 cache (a subset of its rows).
- Select a submatrix of previously selected submatrix of B that fits into the L1 cache, and use it to do the kernel update (a subset of its rows).

Here is a good [visualization](https://jukkasuomela.fi/cache-blocking-demo/) by Jukka Suomela (it shows different approaches; we use the last one).

We could have started with A, but this would be slower. Note that during the kernel execution, we are reading the elements of $A$ slower than elements of $B$: we are fetching and broadcasting just one element, and then we multiply it with $16$ elements of $B$, so we need to store $B$ in cache, and the last stage be about selecting B in cache.

We can implement it with three more outer `for` loops:

```c++
const int s3 = 64;  // how many columns of B to select
const int s2 = 120; // how many rows of A to select 
const int s1 = 240; // how many rows of B to select

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
                    kernel(a, (vec*) b, (vec*) c, x, y, i1, std::min(i1 + s1, n), ny);
```

These outer `for` loops are sometimes called *macro-kernel* (as opposed to the *micro-kernel* that only updates a 6x16 submatrix).

It completely removes the memory bottleneck:

![](../img/mm-blocked-plot.svg)

The performance is no longer seriously affected by the problem size:

![](../img/mm-blocked-barplot.svg)

Notice the dip at $1536$ is still there. Cache associativity affects the effective cache size. We need to adjust the step constants or insert holes into the layout to mitigate this.

## Optimization

We need a few more optimizations to reach the performance limit:

- Remove memory allocation and just operate on the arrays that we are given (note that we don't need to do anything with `a` as we are reading just one element at a time, and we can use unaligned `store` for `c` as we only use it rarely).
- Get rid of the `std::min` so that the size parameters are mostly constant and can be embedded into the machine code.
- Rewrite the micro-kernel by hand using 12 variables (the compiler seems to have a problem with keeping them fully in registers).

Effectively supporting weird sizes requires a bit more work, and this is the reason why we benchmarked at an array sizes that are divisible by $48 = \frac{6 \cdot 16}{\gcd(6, 16)}$.

Avoiding moving anything pays off. These improvements sum up and give us a 50% improvement:

![](../img/mm-noalloc.svg)

We are actually not that far from the theoretical performance limit — which can be calculated as the throughput of the SIMD lane width times the fma instruction times the clock frequency:

$$
\underbrace{8}_{SIMD} \cdot \underbrace{2}_{thr.} \cdot \underbrace{2 \cdot 10^9}_{cycles/sec} = 32 \; GFLOPS \;\; (3.2 \cdot 10^{10})
$$

A more realistic comparison is some practical library, such as [https://www.openblas.net/](OpenBLAS). We just call it from Python using [numpy](/hpc/complexity/languages/#blas), so there may be some minor overhead, but reaching 80% of theoretical performance seems plausible (matrix multiplication is not the only thing that CPUs are made for):

![](../img/mm-blas.svg)

We've reached ~93% of BLAS and ~75% of the theoretical performance limit. Which is really great for what is basically 40 lines of C.

Interestingly, the whole thing can be rolled into one large `for` loop:

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
                                += (vec{} + a[x * n + i * n + k])
                                   * b[n / 8 * k + y / 8 + j];
```

(Assuming that we are in 2050 and using the 35th version of GCC, which finally properly manager not to screwing up with register spilling.)

## Generalizations

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

The algorithm was originally designed by Kazushige Goto, and it is the basis of GotoBLAS and OpenBLAS. The author himself described it and some other aspects in more detail in "[Anatomy of High-Performance Matrix Multiplication](https://www.cs.utexas.edu/~flame/pubs/GotoTOMS_revision.pdf)".

The exposition style is inspired by "[Programming Parallel Computers](http://ppc.cs.aalto.fi/)" course by Jukka Suomela, which features a [similar case study](http://ppc.cs.aalto.fi/ch2/) on speeding up the distance product.
