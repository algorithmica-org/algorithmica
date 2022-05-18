---
title: Cache-Oblivious Algorithms
weight: 7
---

In the context of the [external memory model](../model), there are two types of efficient algorithms:

- *Cache-aware* algorithms that are efficient for *known* $B$ and $M$.
- *Cache-oblivious* algorithms that are efficient for *any* $B$ and $M$.

For example, [external merge sorting](../sorting) is a cache-aware, but not cache-oblivious algorithm: we need to know the memory characteristics of the system, namely the ratio of available memory to the block size, to find the right $k$ to perform $k$-way merge sort.

Cache-oblivious algorithms are interesting because they automatically become optimal for all memory levels in the cache hierarchy, and not just the one for which they were specifically tuned. In this article, we consider some of their applications in matrix calculations.

## Matrix Transposition

Assume we have a square matrix $A$ of size $N \times N$, and we need to transpose it. The naive by-definition approach would go something like this:

```cpp
for (int i = 0; i < n; i++)
    for (int j = 0; j < i; j++)
        swap(a[j * N + i], a[i * N + j]);
```

Here we used a single pointer to the beginning of the memory region instead of a 2d array to be more explicit about its memory operations.

The I/O complexity of this code is $O(N^2)$ because the writes are not sequential. If you try to swap the iteration variables, it will be the other way around, but the result is going to be the same.

### Algorithm

The *cache-oblivious* algorithm relies on the following block matrix identity:

$$
\begin{pmatrix}
A & B \\
C & D
\end{pmatrix}^T=
\begin{pmatrix}
A^T & C^T \\
B^T & D^T
\end{pmatrix}
$$

It lets us solve the problem recursively using a divide-and-conquer approach:

1. Divide the input matrix into 4 smaller matrices.
2. Transpose each one recursively.
3. Combine results by swapping the corner result matrices.

Implementing D&C on matrices is a bit more complex than on arrays, but the main idea is the same. Instead of copying submatrices explicitly, we want to use "views" into them, and also switch to the naive method when the data starts fitting in the L1 cache (or pick something small like $32 \times 32$ if you don't know it in advance). We also need to carefully handle the case when we have odd $n$ and thus can't split the matrix into 4 equal submatrices.

```cpp
void transpose(int *a, int n, int N) {
    if (n <= 32) {
        for (int i = 0; i < n; i++)
            for (int j = 0; j < i; j++)
                swap(a[i * N + j], a[j * N + i]);
    } else {
        int k = n / 2;

        transpose(a, k, N);
        transpose(a + k, k, N);
        transpose(a + k * N, k, N);
        transpose(a + k * N + k, k, N);
        
        for (int i = 0; i < k; i++)
            for (int j = 0; j < k; j++)
                swap(a[i * N + (j + k)], a[(i + k) * N + j]);
        
        if (n & 1)
            for (int i = 0; i < n - 1; i++)
                swap(a[i * N + n - 1], a[(n - 1) * N + i]);
    }
}
```

The I/O complexity of the algorithm is $O(\frac{N^2}{B})$, as we only need to touch roughly half the memory blocks during each merge stage, meaning that on each stage our problem becomes smaller.

Adapting this code for the general case of non-square matrices is left as an exercise to the reader.

## Matrix Multiplication

Next, let's consider something slightly more complex: matrix multiplication.

$$
C_{ij} = \sum_k A_{ik} B_{kj}
$$

The naive algorithm just translates its definition into code:

```cpp
// don't forget to initialize c[][] with zeroes
for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++)
        for (int k = 0; k < n; k++)
            c[i * n + j] += a[i * n + k] * b[k * n + j];
```

It needs to access $O(N^3)$ blocks in total as each scalar multiplication needs a separate block read.

One well-known optimization is to transpose $B$ first:

```cpp
for (int i = 0; i < n; i++)
    for (int j = 0; j < i; j++)
        swap(b[j][i], b[i][j])
// ^ or use our faster transpose from before

for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++)
        for (int k = 0; k < n; k++)
            c[i * n + j] += a[i * n + k] * b[j * n + k]; // <- note the indices
```

Whether the transpose is done naively or with the cache-oblivious method we previously developed, the matrix multiplication with one of the matrices transposed would work in $O(N^3/B + N^2)$ as all memory accesses are now sequential.

It seems like we can't do better, but it turns out we can.

### Algorithm

Cache-oblivious matrix multiplication relies on essentially the same trick as the transposition. We need to divide the data until it fits into lowest cache (i.e., $N^2 \leq M$). For matrix multiplication, this equates to using this formula:

$$
\begin{pmatrix}
A_{11} & A_{12} \\
A_{21} & A_{22} \\
\end{pmatrix} \begin{pmatrix}
B_{11} & B_{12} \\
B_{21} & B_{22} \\
\end{pmatrix} = \begin{pmatrix}
A_{11} B_{11} + A_{12} B_{21} & A_{11} B_{12} + A_{12} B_{22}\\
A_{21} B_{11} + A_{22} B_{21} & A_{21} B_{12} + A_{22} B_{22}\\
\end{pmatrix}
$$

It is slightly harder to implement though because we now have a total of 8 recursive matrix multiplications:

```cpp
void matmul(const float *a, const float *b, float *c, int n, int N) {
    if (n <= 32) {
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                for (int k = 0; k < n; k++)
                    c[i * N + j] += a[i * N + k] * b[k * N + j];
    } else {
        int k = n / 2;

        // c11 = a11 b11 + a12 b21
        matmul(a,     b,         c, k, N);
        matmul(a + k, b + k * N, c, k, N);
        
        // c12 = a11 b12 + a12 b22
        matmul(a,     b + k,         c + k, k, N);
        matmul(a + k, b + k * N + k, c + k, k, N);
        
        // c21 = a21 b11 + a22 b21
        matmul(a + k * N,     b,         c + k * N, k, N);
        matmul(a + k * N + k, b + k * N, c + k * N, k, N);
        
        // c22 = a21 b12 + a22 b22
        mul(a + k * N,     b + k,         c + k * N + k, k, N);
        mul(a + k * N + k, b + k * N + k, c + k * N + k, k, N);

        if (n & 1) {
            for (int i = 0; i < n; i++)
                for (int j = 0; j < n; j++)
                    for (int k = (i < n - 1 && j < n - 1) ? n - 1 : 0; k < n; k++)
                        c[i * N + j] += a[i * N + k] * b[k * N + j];
        }
    }
}
```

Because there are many other factors in play here, we are not going to benchmark this implementation, and instead just do its theoretical performance analysis in external memory model.

### Analysis

Arithmetic complexity of the algorithm remains is the same, because the recurrence

$$
T(N) = 8 \cdot T(N/2) + \Theta(N^2)
$$

is solved by $T(N) = \Theta(N^3)$.

It doesn't seem like we "conquered" anything yet, but let's think about its I/O complexity:

$$
T(N) = \begin{cases}
O(\frac{N^2}{B}) & N \leq \sqrt M & \text{(we only need to read it)} \\
8 \cdot T(N/2) + O(\frac{N^2}{B}) & \text{otherwise}
\end{cases}
$$

The recurrence is dominated by $O((\frac{N}{\sqrt M})^3)$ base cases, meaning that the total complexity is

$$
T(N) = O\left(\frac{(\sqrt{M})^2}{B} \cdot \left(\frac{N}{\sqrt M}\right)^3\right) = O\left(\frac{N^3}{B\sqrt{M}}\right)
$$

This is better than just $O(\frac{N^3}{B})$, and by quite a lot.

### Strassen Algorithm

In a spirit similar to the Karatsuba algorithm, matrix multiplication can be decomposed in a way that involves 7 matrix multiplications of size $\frac{n}{2}$, and the master theorem tells us that such divide-and-conquer algorithm would work in $O(n^{\log_2 7}) \approx O(n^{2.81})$ time and a similar asymptotic in the external memory model.

This technique, known as the Strassen algorithm, similarly splits each matrix into 4:

$$
\begin{pmatrix}
C_{11} & C_{12} \\
C_{21} & C_{22} \\
\end{pmatrix}
=\begin{pmatrix}
A_{11} & A_{12} \\
A_{21} & A_{22} \\
\end{pmatrix}
\begin{pmatrix}
B_{11} & B_{12} \\
B_{21} & B_{22} \\
\end{pmatrix}
$$

But then it computes intermediate products of the $\frac{N}{2} \times \frac{N}{2}$ matrices and combines them to get matrix $C$:

$$
\begin{aligned}
   M_1 &= (A_{11} + A_{22})(B_{11} + B_{22})   & C_{11} &= M_1 + M_4 - M_5 + M_7
\\ M_2 &= (A_{21} + A_{22}) B_{11}             & C_{12} &= M_3 + M_5
\\ M_3 &= A_{11} (B_{21} - B_{22})             & C_{21} &= M_2 + M_4
\\ M_4 &= A_{22} (B_{21} - B_{11})             & C_{22} &= M_1 - M_2 + M_3 + M_6
\\ M_5 &= (A_{11} + A_{12}) B_{22}
\\ M_6 &= (A_{21} - A_{11}) (B_{11} + B_{12})
\\ M_7 &= (A_{12} - A_{22}) (B_{21} + B_{22})
\end{aligned}
$$

You can verify these formulas with simple substitution if you feel like it.

As far as I know, none of the mainstream optimized linear algebra libraries use the Strassen algorithm, although there are [some prototype implementations](https://arxiv.org/pdf/1605.01078.pdf) that are efficient for matrices larger than 2000 or so.

This technique can and actually has been extended multiple times to reduce the asymptotic even further by considering more submatrix products. As of 2020, current world record is $O(n^{2.3728596})$. Whether you can multiply matrices in $O(n^2)$ or at least $O(n^2 \log^k n)$ time is an open problem.

## Further Reading

For a solid theoretical viewpoint, consider reading [Cache-Oblivious Algorithms and Data Structures](https://erikdemaine.org/papers/BRICS2002/paper.pdf) by Erik Demaine.
