---
title: Spacial and Temporal Locality
weight: 1
---

In some environments, the programmer has no direct control over caching. Moreover, sometimes we don't even know the high-level characteristics of the cache hierarchy, such as the memory size of each layer, the block size, the strategy used for cache eviction, or even the number of cache layers.

In this article, we continue designing algorithms for the external memory model and address the problem of assessing I/O performance when some details of the cache system are unknown.

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

In practice, there is still some overhead associated with the recursion, and for of this reason, it makes sense to use hybrid algorithms where we don't go all the way down to the base case and instead switch to the iterative code on lower levels of recursion.

### Dynamic Programming

A similar reasoning can be applied to the implementations of dynamic programming algorithms.

Consider the classic knapsack problem, where we got $n$ items with integer costs $c_i$, and we need to pick a subset of items with maximum total cost that does not exceed a given constant $w$.

The way to solve it is to introduce the state of dynamic $f[i, k]$, which corresponds to the maximum total cost less than $k$ can be achieved having already considered and excluded the first $i$ items. It can be updated in $O(1)$ time per entry, by either taking or not taking the $i$-th item and using further states of the dynamic to compute the optimal decision for each state.

Python has a handy `lru_cache` decorator for implementing it with memoized recursion:

```python
@lru_cache
def f(i, k):
    if i == n or k == 0:
        return 0
    if w[i] > k:
        return f(i + 1, k)
    return max(f(i + 1, k), c[i] + f(i + 1, k - w[i]))
```

When computing $f[n, w]$, the recursion may possibly visit $O(n \cdot w)$ different states, which is asymptotically efficient, but rather slow in reality. Even after nullifying the overhead of Python recursion and the hash table queries required for the LRU cache to work, it would still be slow because it does random I/O throughout most of the execution.

What we can do instead is to create a 2d array for the dynamic and replace memoized recursion with a nice nested loop like this:

```cpp
int f[N + 1][W + 1];

for (int i = n - 1; i >= 0; i++)
    for (int k = 0; k <= W; k++)
        f[i][k] = w[i] > k ? f[i + 1][k] : max(f[i + 1][k], c[i] + f[i + 1][k - w[i]]);
```

Notice that we are only using the previous layer of the dynamic to calculate the next one. This means that if we can store one layer in cache, we would only need to write $O(\frac{n \cdot w}{B})$ blocks in external memory.

Moreover, if we only need the answer, we don't actually have to store the whole 2d array, but only the last layer. This lets us use just $O(w)$ memory by maintaining a single array of $w$ values. To simplify the code, we can slightly change the dynamic to store a binary value: whether it is possible to get the sum of exactly $k$ using the items that we have consider. This dynamic is even faster to compute:

```cpp
bool f[W + 1] = {}; // this zero-fills the array
f[0] = 1;
for (int i = 0; i < n; i++)
    for (int x = W - a[i]; x >= 0; x--)
        f[x + a[i]] |= f[x];
```

As a side note, now that it only uses simple bitwise operations, it can be optimized further by using a bitset:

```cpp
std::bitset<W + 1> b;
b[0] = 1;
for (int i = 0; i < n; i++)
    b |= b << c[i];
```

Surprisingly, there is still some room for improvement, and we will come back ot this problem later.

### Sparse Table

*Sparse table* is a *static* data structure often used for solving static RMQ problem and computing any similar *idempotent reductions* in general. It can be formally defined as a 2d array of size $\log n \times n$:

$$
t[k][i] = \min \{ a_i, a_{i+1}, \ldots, a_{i+2^k-1} \}
$$

In plain English: we store the minimum on each segment whose length is a power of two. 

Such array can be used for calculating minima on arbitrary segments in constant time, because for each segment there are two possibly overlapping segments whose sizes is the same power of two, the union of which gives the whole segment.

![](../img/sparse-table.png)

This means that we can just take the minimum of these two precomputed minimums as the answer:

```cpp
int rmq(int l, int r) { // half-interval [l; r)
    int t = __lg(r - l);
    return min(mn[t][l], mn[t][r - (1 << t)]);
}
```

The `__lg` function is an intrinsic available in GCC that calculates binary logarithm of a number rounded down. Internally it uses already familiar `clz` ("count leading zeros") instruction and subtracts this count from 32 in case of a 32-bit integer, and thus takes just a few cycles.

The reason why I bring it up in this article is because there are multiple alternative ways it can be built, with different performance in terms of I/O operations. In general, sparse table can be built in $O(n \log n)$ time in dynamic programming fashion by iterating in the order of increasing $i$ or $k$ and applying the following identity:

$$
t[k][i] = \min(t[k-1][i], t[k-1][i+2^{k-1}])
$$

Now, there are two design choices to make: whether the log-size $k$ should be the first or the second dimension, and whether to iterate over $k$ and then $i$ or the other way around. This means that there are of $2×2=4$ ways to build it, and here is the optimal one:

```cpp
int mn[logn][maxn];

memcpy(mn[0], a, sizeof a);

for (int l = 0; l < logn - 1; l++)
    for (int i = 0; i + (2 << l) <= n; i++)
        mn[l + 1][i] = min(mn[l][i], mn[l][i + (1 << l)]);
```

This is the only combination of the memory layout and the iteration order that results in beautiful linear passes that work ~3x faster. As an exercise, consider the other three variants and think about *why* they are slower.

### Array-of-Structs and Struct-of-Arrays

Suppose you want to implement a binary tree and store its fields in separate arrays like this:

```cpp
int left_child[maxn], right_child[maxn], key[maxn], size[maxn];
```

Such memory layout, when we store each field separately from others, is called *struct-of-arrays* (SoA). In most cases, when implementing tree operations, you access a node and shortly after request all or most of its data. If these fields are stored separately, this would mean that they are also located in different memory blocks. It some of the requested fields are cached while others are not, you would still have to wait for the data in the lowest layer of cache to arrive.

In contrast, if it was instead stored as an array-of-structs (AoS), you would need ~4 times less block reads as all the data of the node is stored in the same block and fetched at once:

```cpp
struct Node {
    int left_child, right_child, key, size;
};

Node t[maxn];
```

So the AoS layout is beneficial for data structures, but SoA still has good uses: while it is worse for searching, it is much better for linear scanning.

This difference in design is important in data processing applications. For example, databases can be either row-based or columnar:

- *Row-based* storage formats are used when you need to search for a limited amount of objects in a large dataset, and fetch all or most of their fields.
- *Columnar* storage formats are used for big data processing and analytics, where you need to scan through everything anyway to calculate certain statistics.

Columnar formats have an additional advantage that you can only read the fields that you need, as different fields are stored in separate external memory regions.
