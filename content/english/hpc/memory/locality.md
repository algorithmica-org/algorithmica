---
title: Cache Locality
weight: 2
---

In some environments, the programmer has no direct control over caching. Moreover, sometimes we don't even know the high-level characteristics of the cache hierarchy, such as the memory size of each layer, the block size, the strategy used for cache eviction, or even the number of cache layers.

In this context, there are two types of efficient [external memory](../external) algorithms:

- *Cache-aware* algorithms that are efficient for *known* $B$ and $M$.
- *Cache-oblivious* algorithms that are efficient for *any* $B$ and $M$.

For example, external merge sort is cache-aware, but not cache-oblivious: we need to know memory characteristics of the system, namely the ratio of available memory to the block size, to find the right $k$ to do k-way merge sort.

Cache-oblivious algorithms are interesting because they automatically become optimal for all memory levels in the cache hierarchy, and not just the one for which they were tuned. In this article, we continue designing algorithms for the external memory model and address the problem of assessing I/O performance when some details of the cache system are unknown.

## Caching Strategies

When you run out of inner memory to store your data, you need to delete one block to make space for a new one. Since caching usually happens in the background, you need a concrete rule for deciding which data to retain in the cache, called *eviction policy*.

This rule can be arbitrary, but there are several popular choices:

- First in first out (FIFO): simply evict the earliest added block, without any regard to how often it was accessed before (the same way as a FIFO queue).
- Least recently used (LRU): evict the block that has not been accessed for the longest period of time.
- Last in first out (LIFO) and most recently used (MRU): the opposite of the previous two. It seems harmful to delete the hottest blocks, but there are scenarios where these policies are optimal, such as repeatedly looping around a file in a cycle.
- Least-frequently used (LFU): counts how often each block has been requested, and discards the one used least often. There are variations that account for changing access patterns over time, such as using a time window to only consider the last $n$ accesses, or using exponential averaging to give recent accesses more weight.
- Random replacement (RR): discard a block randomly. The advantage is that it does not need to maintain any data structures with block information.

There is a natural trade-off between the accuracy of eviction policies and the additional overhead due to the complexity of their implementations. For a CPU cache, you need a simple policy that can be easily implemented in hardware with almost zero latency, while in more slow-paced and plannable settings such as Netflix deciding in which data centers to store their movies or Google Drive optimizing where to store user data, it makes sense to use more complex policies, possibly involving machine learning to predict when the data is going to be accessed next.

### Implementing Caching

This is not always a trivial task to find the right block to evict in a reasonable time. While CPU caches are implemented in hardware (usually as a variation of LRU), higher-level eviction policies have to rely on software to store certain statistics about the blocks and maintain data structures on top of them to speed up the process.

For example, let's think about what it takes to implement an LRU cache. Assume we are storing some moderately large objects — say, we need to develop a cache for a database, there both the requests and replies are medium-sized strings in some SQL dialect, so the overhead of our structure is small, but non-negligible.

<!-- https://www.geeksforgeeks.org/lru-cache-implementation/ -->

First of all, we need a hash table to find the data itself. Since we are working with large variable-length strings, it makes sense to use a hash of the query as the key and a pointer to the heap-allocated result string as the value.

To implement the LRU logic, the simplest approach would be to create a queue where we put the current time and IDs/keys of objects when we access them, and also store for each object when was the last time it was accessed (not necessarily as a timestamp — any increasing counter will suffice).

Now, when we need to free up space, we can find the least recently used object by popping elements from the front of the queue — but we can't just delete them, because it may be that they were accessed again since their record was added to the queue. So we need to check if the timestamp when we put them in queue matches the timestamp when they were last accessed, and only then free up the memory.

The only problem here is that we add an entry to the queue each time a block is accessed, and only remove entries when we have a cache miss and start popping them off from the front until we have a match. This may lead to the queue overflowing, and to counter this, instead of adding an entry and forgetting about it, we can move it to the end of the queue on a cache hit right away.

To support this, we need to implement the queue over a doubly linked list and store a pointer to the block's node in the queue in the hash table. Then, when we have a cache hit, we follow the pointer and remove the node from the linked list in constant time, and add a newer node to the end of the queue. This way, at any point in time, there would be exactly as many nodes in the queue as we have objects, and the memory overhead will be guaranteed to be constant per cache entry.

As an exercise, try to think about ways to implement other caching strategies. It is quite fun, I assure you.

### Optimal Caching

Apart from aforementioned strategies, there is also what's called *Bélády algorithm*, often denoted as $OPT$ or $MIN$, which determined which blocks should be retained in the *optimal* policy for a given sequence of queries.

The way it achieves it is simple: we can always greedily keep the *latest-to-be-used* block, and it can be shown by contradiction that doing so is always one of the optimal solutions. The downside of this method is that you either need to have these queries in advance or somehow be able to predict the future.

But the good thing is that, in terms of asymptotic complexity, it doesn't really matter which particular method is used. [Sleator & Tarjan showed](https://www.cs.cmu.edu/~sleator/papers/amortized-efficiency.pdf) that in most cases, the performance of popular policies such as $LRU$ differs from $OPT$ just by a constant factor.

**Theorem.** Let $LRU_M$ and $OPT_M$ denote the number of blocks a computer with $M$ internal memory would need to access while executing the same algorithm following the least recently used cache replacement policy and the theoretical minimum respectively. Then

$$
LRU_M \leq 2 \cdot OPT_{M/2}
$$

The main idea of the proof is to consider the "worst case" scenario. For LRU it would be the repeating series of $\frac{M}{B}$ distinct blocks: each block is new and so LRU has 100% cache misses. Meanwhile, $OPT_{M/2}$ would be able to cache half of them (but not more, because it only has half the memory). Thus $LRU_M$ needs to fetch double the number of blocks that $OPT_{M/2}$ does, which is basically what is expressed in the inequality, and anything better for $LRU$ would only weaken it.

![Dimmed are the blocks cached by OPT (but note cached by LRU)](../img/opt.png)

This is a very relieving result. It means that, at least in terms of asymptotic I/O complexity, you can just assume that the eviction policy is either LRU or OPT — whichever is easier for you — do complexity analysis with it, and the result you get will normally transfer to any other reasonable cache replacement policy.

## Data Locality

Abstracting away from the minor details of the cache system helps a lot when designing algorithms. Instead of calculating theoretical cache hit rates, it often makes more sense to reason about cache performance in more abstract qualitative terms.

We can talk about the degree of cache reuse primarily in two ways:

- *Temporal locality* refers to the repeated access of the same data within a relatively small time duration, such that the data likely remains cached between the requests.
- *Spacial locality* refers to the use of elements relatively close to each other in terms of their memory locations, such that they are likely fetched in the same memory block.

In other words, temporal locality is when it is likely that this same memory location will soon be requested again, while spacial locality is when it is likely that a nearby location will be requested right after.

We will now go through some examples to show how these concepts can help in optimization.

### Depth-First and Breadth-First

Consider a divide-and-conquer algorithm such as merge sort. There are two approaches to implementing it:

- We can implement it recursively, or "depth-first", the way it is normally implemented: sort the left half, sort the right half, and then merge the results.
- We can implement it iteratively, or "breadth-first": do the lowest "layer" first, looping through the entire dataset and comparing odd elements with even elements, then merge the first two elements with the second two elements, the third two elements with the fourth two elements and so on.

It seems like the second approach is more cumbersome, but faster — because recursion is always slow, right?

But this is not the case for this and many similar divide-and-conquer algorithms. Although the iterative approach has the advantage of only doing sequential I/O, the recursive approach has much better temporal locality: when a segment fully fits into cache, it stays there for all lower layers of recursion, resulting in better access times later on.

In fact, since we only need $O(\log \frac{N}{M})$ layers until this happens, we would only need to read $O(\frac{N}{B} \log \frac{N}{M})$ blocks in total, while in the iterative approach the entire array will be read from scratch $O(\log N)$ times no matter what. The results in the speedup of $O(\frac{\log N}{\log N - \log M})$, which may be up to an order of magnitude.

In practice, there is some overhead associated with the recursion, and for of this reason, it makes sense to use hybrid algorithms where we don't go all the way down to the base case and instead switch to the iterative code on lower levels of recursion.

### Dynamic Programming and Memoization

TODO

A similar reasoning can be applied to the implementations of dynamic programming algorithms.

Consider the classic knapsack problem, where .

Python has a handy `lru_cache` decorator for solving it with recursion:

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

Todo: mention bitset

Note that each layer is computed and then accessed exactly once right after (you actually need $O(W)$ memory which could all fit into L1 cache).

### Iteration Order

Sparse table is a *static* data structure for computing *idempotent reductions*. It is frequently used to solve static RMQ.

To build it, you need to compute the function for all power-of-two length segments You can do it in DP fashion by using already processed segments:

```cpp
int mn[logn][maxn];

for (int l = 0; l < logn - 1; l++)
    for (int i = 0; i + (2 << l) <= n; i++)
        mn[l+1][i] = min(mn[l][i], mn[l][i + (1 << l)]);
```

There are a total of 2×2=4 ways to build it, only one of them yields beautiful linear passes that work ~3x faster.

### Array-of-Structs and Struct-of-Arrays

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

We use only 7 multiplications instead of 8, so arithmetic complexity is $O(n^{\log_2 7}) \approx O(n^{2.81})$.

As of 2020, current world record is $O(n^{2.3728596})$

## Further Reading

[Cache-Oblivious Algorithms and Data Structures](https://erikdemaine.org/papers/BRICS2002/paper.pdf) by Erik Demaine.
