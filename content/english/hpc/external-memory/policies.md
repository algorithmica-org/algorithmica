---
title: Eviction Policies
weight: 6
---

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
