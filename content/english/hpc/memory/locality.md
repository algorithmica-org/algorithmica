---
title: Cache Locality
weight: 2
draft: true
---

In some environments, we don't have a direct control over caching — that is, we can't control on which cache levels the data is going to reside. Moreover, sometimes we don't even know the characteristics, such as memory on each layer, block size, how caching happens exactly or even the number of layers.

An algorithm is called *cache-efficient*, if it is efficient in terms of its I/O operations. There are two types of cache-efficient algorithms:

* Cache-aware: efficient with *known* $B$ and $M$
* Cache-oblivious: efficient for *any* $B$ and $M$

For example, external merge sort is cache-aware, but not cache-oblivious: we need to know memory characteristics, namely the ratio of memory to block size, to find the right $k$ to do k-way merge sort.

Cache-oblivious algorithms are cool because they are optimal for all memory levels

Tuning algorithms for particular environments is always beneficial. But yet, we still need useful methods for assessing I/O performance of algorithms in such environments, which is the topic of this article.

## Caching Strategies

Eviction policy is the method for deciding which data to retain in the cache.

One important aspect of any caching mechanism is its *eviction policy*. It regulates which blocks we need to keep in memory if we run out of it.

There are several popular choices:

* $FIFO$: first in, first out
* $LRU$: least recently used. This is like preferring beer with later expiration dates.

### Implementing Cache

All these policies need different data structures to be implemented. This is usually what happens for high-level cache, where you need to cache a server request or something like that.

Hardware-defined for CPU caches, programmable for everything larger. In CPUs, it is controlled by hardware, not software. For simplicity, programmer can assume that least recently used (LRU) policy is used, which just evicts the item that hasn’t been used for the longest amount of time.

What do you need to implement LRU cache?

Assume we are storing some large objects — say, medium-sized strings that are the result of some SQL request — so that the overhead of the structure itself is not so large.

You create a hash tables where you put the objects, and also store the timestamps of the last access somewhere nearby. You need to maintain a queue with pointers to the elements in the hash table.

When you add an object that wasn't added before, you need to check if you need to remove some other object by cycling through the queue. Each time you look up a position in the hash table and its time stamp.

As an exercise, think about ways to implement other caching strategies.

### Optimal Caching

Apart from aforementioned strategies, there is also $OPT$, the "optimal" one, that greedily removes the latest-to-be-used block, which can be shown by contradiction to always be optimal. The downside is that you need to able to predict the future to do that.

Good thing is, in terms of asymptotic complexity, it doesn't really matter which particular method is used. [Sleator & Tarjan showed in 1985](https://www.cs.cmu.edu/~sleator/papers/amortized-efficiency.pdf) that performance of LRU differs from OPT just by a constant factor.

**Theorem.**

$$
LRU_M \leq 2 \cdot OPT_{M/2}
$$

Sketch of a proof:

* Consider "worst case" scenario: repeating series of $\frac{M}{B}$ distinct blocks
* For $LRU$, each block is new and so it has 100% cache misses
* $OPT_{M/2}$ would be able to cache half of them and thus halve the time
* Anything better for $LRU$ would only strengthen this inequality

![Dimmed are the cached blocks](../img/opt.png)

This is a relieving result. At least in terms of asymptotic, you can just assume that the eviction policy is LRU, and in most cases the I/O complexity will be correct with any other adequate policy also.

## Data Locality

Abstracting away from how cache works helps a lot when designing algorithms.

Sometimes, instead of calculating theoretical cache hit rates, it makes more sense to reason about cache performance in more abstract qualitative terms.

*Temporal locality* is an access pattern where if at one point a particular item is requested, it is likely that this same location will be requested again in the near future. This is like fetching the same type of beer over and over again.

*Spacial locality* is an access pattern where if a memory location is requested, it is likely that a nearby memory locations will be requested again in the near future. This is like storing the kinds of beer that you like on the same shelf.

In other words, temporal locality is when it's likely that this same location will soon be requested again, while spacial locality is when it's likely that a nearby location will be requested right after. These are both qualitative concepts.

We will now go through some short case studies to illustrate the idea.

### Depth-First vs Breadth-First

Consider a divide-and-conquer algorithm such as merge sort. There are two ways to go about implementing it:

- We could implement it recursively like we'd normally do.
- We could do the lowest stage first, looping through the entire dataset and comparing odd elements with even elements.

A lot of algorithms like this can be implemented in one of two ways. Both have their own advantages:

* Recursive: you would be able to fit smaller datasets into cache (temporal locality)
* Iterative: you would be able to do sequential i/o (spacial locality)

Partially because of this reason, it makes sense to stop the recursion not on the base case, but slightly before that.

In general, you want to do divide-and-conquer depth-first most of the time.

### Dynamic Programming

For dynamic programming, there are two implementation strategies as well.

Consider the classic knapsack problem. Python has a handy `lru_cache` decorator for solving it with recursion:

```python
@lru_cache
def f(i, k):
    if i == n or k == 0:
        return 0
    if w[i] > k:
        return f(i + 1, k)
    return max(f(i + 1, k), c[i] + f(i + 1, k - w[i]))
```

The recursion is extremely slow not because its recursion or checking with a hash table (although it is a contributing factor here too), but because it does random I/O throughout most of the execution.

What we can do instead is to replace it with a nice cycle like this:

```cpp
int f[N+1][W+1];

for (int i = n - 1; i >= 0; i++)
    for (int k = 0; k <= W; k++)
        f[i][k] = (w[i] > k ? f[i+1][k] : max(f[i+1][k], c[i] + f[i+1][k-w[i]]));
```

Note that each layer is computed and then accessed exactly once right after (you actually need $O(W)$ memory which could all fit into L1 cache).

### Iteration Order Matters

Sparse table is a *static* data structure for computing *idempotent reductions*. It is frequently used to solve static RMQ.

To build it, you need to compute the function for all power-of-two length segments You can do it in DP fashion by using already processed segments:

```cpp
int mn[logn][maxn];

for (int l = 0; l < logn - 1; l++)
    for (int i = 0; i + (2 << l) <= n; i++)
        mn[l+1][i] = min(mn[l][i], mn[l][i + (1 << l)]);
```

There are a total of 2×2=4 ways to build it, only one of them yields beautiful linear passes that work ~3x faster.

### Array-of-Structs vs Struct-of-Arrays

Suppose you build a binary tree and store it like this (SoA):

```cpp
int left_child[maxn], right_child[maxn], key[maxn], size[maxn];
```

It it was stored like this (AoS), you would need ~4 times less block reads:

```cpp
struct Data {
    int left_child, right_child, key, size;
};

Data data[maxn];
```

AoS is better for searching, SoA is better for scanning.

Data bases can be document-based or columnar. Row format is used when you need to search for a limited amount of objects in a large dataset. Columnar formats are used for big data processing and analytics, where you need to scan through everything anyway. You have the advantage of reading just the fields you need.

## Matrix Transpose

Assume we have a square matrix $A$ of size $N \times N$.

Naive way to transpose it:

```cpp
for (int i = 0; i < n; i++)
    for (int j = 0; j < i; j++)
        swap(a[j][i], a[i][j])
```

I/O complexity is $O(N^2)$, because writes are not sequential. If you swap iteration variables it's going to be the same but for writes.

*Cache-oblivious algorithm* would be to do this:

1. Divide the input matrix into 4 smaller matrices.
2. Transpose each one recursively.
3. Combine results by swapping the corner result matrices.
4. Stop until it fits into cache.

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

Complexity: $O(\frac{N^2}{B})$. It makes sense to pick something like 32x32 if you don't know cache size beforehand.

### Implementation

Implementing D&C on matrices is a bit more complex than on arrays,
but the idea is the same: we want to use "virtual" matrices instead of copying them

```cpp
int *a;
int N;

// transpose a square submatrix of size n starting at (x, y)
// a[x:x+n][y:y+n]
void transpose(int x, int y, int n) {
    a[x * N + y]
    // todo
}
```

```cpp
template<typename T>
struct Matrix {
    int x, y, n, N;
    T* data;
    T* operator[](int i) { return data + (x + i) * N + y; }
    Matrix<T> subset(int _x, int _y, int _n) { return {_n, _x, _y, N, data}; }

    Matrix<T> transpose() {
        if (n <= 32) {
            for (int i = 0; i < n; i++)
                for (int j = 0; j < i; j++)
                    swap((*this)[j][i], (*this)[i][j]);
        } else {
            auto A = subset(x, y, n / 2).transpose();
            auto B = subset(x + n / 2, y, n / 2).transpose();
            auto C = subset(x, y + n / 2, n / 2).transpose();
            auto D = subset(x + n / 2, y + n / 2, n / 2).transpose();
            for (int i = 0; i < n; i++)
                for (int j = 0; j < n; j++)
                    swap(B[i][j], C[i][j]);
        }

        return *this;
    }
};
```

Rectangular and non-power-of-two matrices is left as an exercise to the reader.

## Matrix Multiplication

Next, let's consider something slightly more complex: matrix multiplication.

$$
C_{ij} = \sum_k A_{ik} B_{kj}
$$

The naive would be the to transfer its definition:

```cpp
// don't forget to initialize c[][] with zeroes
for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++)
        for (int k = 0; k < n; k++)
            c[i][j] += a[i][k] * b[k][j];
```

Naive? $O(N^3)$: each scalar multiplication needs a new block read 

Many people know that if we just transpose $B$ first? $O(N^3/B + N^2)$

```cpp
for (int i = 0; i < n; i++)
    for (int j = 0; j < i; j++)
        swap(b[j][i], b[i][j])
// ^ or use our faster transpose from before

for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++)
        for (int k = 0; k < n; k++)
            c[i][j] += a[i][k] * b[j][k]; // <- note the indices
```

It seems like we can't do better, but it turns out, we can.

### Divide-and-Conquer

Essentially the same trick: divide data until it fits into lowest cache ($N^2 \leq M$). For matrix multiplication, this is equivalent to using this formula:

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

Arithmetic complexity is the same, because

$$
T(N) = 8 \cdot T(N/2) + O(N^2)
$$

is solved by $T(N) = O(N^3)$.

It doesn't seem like we "conquered" anything yet, but let's think about I/O complexity

$$
T(N) = \begin{cases}
O(\frac{N^2}{B}) & N \leq \sqrt M & \text{(we only need to read it)} \\
8 \cdot T(N/2) + O(\frac{N^2}{B}) & \text{otherwise}
\end{cases}
$$

The recurrence is dominated by $O((\frac{N}{\sqrt M})^3)$ base cases, so the total complexity is

$$
T(N) = O\left(\frac{(\sqrt{M})^2}{B} \cdot (\frac{N}{\sqrt M})^3\right) = O(\frac{N^3}{B\sqrt{M}})
$$

TODO: implementation

We are not going to benchmark it thoroughly, .

### Strassen Algorithm*

$$\begin{pmatrix}
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

Compute intermediate products of $\frac{N}{2} \times \frac{N}{2}$ matrices and combine them to get matrix $C$:

$$
\begin{align}
   M_1 &= (A_{11} + A_{22})(B_{11} + B_{22})   & C_{11} &= M_1 + M_4 - M_5 + M_7
\\ M_2 &= (A_{21} + A_{22}) B_{11}             & C_{12} &= M_3 + M_5
\\ M_3 &= A_{11} (B_{21} - B_{22})             & C_{21} &= M_2 + M_4
\\ M_4 &= A_{22} (B_{21} - B_{11})             & C_{22} &= M_1 - M_2 + M_3 + M_6
\\ M_5 &= (A_{11} + A_{12}) B_{22}
\\ M_6 &= (A_{21} - A_{11}) (B_{11} + B_{12})
\\ M_7 &= (A_{12} - A_{22}) (B_{21} + B_{22})
\end{align}
$$

We use only 7 multiplications instead of 8, so arithmetic complexity is $O(n^{\log_2 7}) \approx O(n^{2.81})$.

As of 2020, current world record is $O(n^{2.3728596})$

