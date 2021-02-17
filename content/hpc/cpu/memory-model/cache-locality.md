---
title: Cache Locality
weight: 5
---

Temporal locality is an access pattern where if at one point a particular item is requested, it is likely that this same location will be requested again in the near future. This is like fetching the same type of beer over and over again.

Spacial locality is an access pattern where if a memory location is requested, it is likely that a nearby memory locations will be requested again in the near future. This is like storing the kinds of beer that you like on the same shelf.

## Data Locality

* Temporal locality: it is likely that this same location will soon be requested again
* Spacial locality: it is likely that a nearby location will be requested right after

Abstracting away from how cache works helps a lot when designing algorithms

---

### Depth-First vs Breadth-First

* A lot of algorithms can be implemented in one of two ways
* Recursive: you would be able to fit smaller datasets into cache (temporal locality)
* Iterative: you would be able to do sequential i/o (spacial locality)

For example, you want to do divide-and-conquer depth-first most of the time

----

Consider the knapsack problem (in Python for simplicity):

```python
@lru_cache
def f(i, k):
    if i == n or k == 0:
        return 0
    if w[i] > k:
        return f(i + 1, k)
    return max(f(i + 1, k), c[i] + f(i + 1, k - w[i]))
```

The recursion is extremely slow not because its recursion,
but because it does random i/o throughout most of the execution

```cpp
int f[N+1][W+1];

for (int i = n - 1; i >= 0; i++)
    for (int k = 0; k <= W; k++)
        f[i][k] = (w[i] > k ? f[i+1][k] : max(f[i+1][k], c[i] + f[i+1][k-w[i]]));
```
<!-- .element: class="fragment" data-fragment-index="1" -->

Note that each layer is computed and then accessed exactly once right after
(you actually need $O(W)$ memory which could all fit into L1 cache)
<!-- .element: class="fragment" data-fragment-index="2" -->

---

### Array-of-Structs and Struct-of-Arrays

Suppose you build a binary tree and store it like this (SoA):

```
int left_child[maxn], right_child[maxn], key[maxn], size[maxn];
```

It it was stored like this (AoS), you would need ~4 times less block reads:

```
struct Data {
    int left_child, right_child, key, size;
};

Data data[maxn];
```

AoS is better for seaching, SoA is better for scanning

----

### Iteration Order Matters

* Sparse table is a *static* data structure for computing *idempotent reductions*
  (on subsegments of arrays, e. g. static RMQ)
* To build it, you need to compute the function for all power-of-two length segments
* You can do it in DP fashion by using already processed segments

```cpp
int mn[logn][maxn];

for (int l = 0; l < logn - 1; l++)
    for (int i = 0; i + (2 << l) <= n; i++)
        mn[l+1][i] = min(mn[l][i], mn[l][i + (1 << l)]);
```

There are a total of 2×2=4 ways to build it,
only one of them yields beautiful linear passes that work ~3x faster

---

## Cache-Efficient Algorithms

* Cache-aware: efficient with *known* $B$ and $M$
* Cache-oblivious: efficient for *any* $B$ and $M$

E. g. external merge sort is cache-aware, but not cache-oblivious

Cache-oblivious algorithms are cool because they are optimal for all memory levels
