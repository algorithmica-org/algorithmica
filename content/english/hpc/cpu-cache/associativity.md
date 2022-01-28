---
title: Cache Associativity
weight: 8
---

- Since implementing "find the oldest among million cache lines" in hardware is unfeasible, each cache layer is split in a number of small "sets", each covering a certain subset of memory locations. *Associativity* is the size of these sets, or, in other terms, how many different "cells" of cache each data location can be mapped to. Higher associativity allows more efficient utilization of cache.


If you looked carefully, you could notice patterns while inspecting the dots below the graph in the [previous experiment](../paging).

These are not just noise: certain step sizes indeed perform much worse than their neighbors.

For example, the stride of 256 corresponding to this loop:

```cpp
for (int i = 0; i < N; i += 256)
    a[i]++;
```

and this one

```cpp
for (int i = 0; i < N; i += 257)
    a[i]++;
```

differ by more than 10x: 256 runs at 0.067 while 257 runs at 0.751.

This is not just a single specific bad value: it is the same for all indices that are multiple of large powers of two, and it continues much further to the right.

![](../img/strides-two.svg)

This effect is due to a feature called *cache associativity*, and an interesting artifact of how CPU caches are implemented in hardware.

### Hardware Caching

When studying memory theoretically using the external memory model, we discussed different ways one can [implement caching policies](/hpc/memory/locality/) in software, and went into detail on particular case of a simple but effective strategy, LRU, which required some non-trivial data manipulation. In the context of hardware, such scheme is called *fully associative cache*.

![Fully associative cache](../img/cache2.png)

The problem with it is that implementing something like that is prohibitively expensive. In hardware, you can implement something when you have 16 entries or so, but it becomes unfeasible when it comes to storing and managing hundreds of cache lines.

We can resort to another, much simpler approach: we could just map each block of 64 bytes in RAM to a cache line which it can possibly occupy. Say if in we have 4096 blocks in memory and 64 cache lines for them, this means that each cache line at any time stores the value of one of $\frac{4096}{64} = 64$ different blocks, along with a "tag" information which helps identifying which block it is.

Simply speaking, the CPU just maintains these cells containing data, and when reading any cell from the main memory the CPU first looks it up in the cache, and if it contains the data, it reads it, and otherwise goes to a higher cache level until it reaches main memory. Simple and beautiful.

![Direct-mapped cache](../img/cache1.png)

Direct-mapped cache is easy to implement, but the problem with it is that the entries can be kicked out way too quickly, leading to lower cache utilization. In fact, we could just bounce between two addresses, leaving

For that reason, we settle for something in-between direct-mapped and fully associative cache: the *set-associative cache*. It splits addresses into groups which separately act as small fully-associative cache.

![Set-associative cache](../img/cache3.png)

*Associativity* is the size of such sets — for example 16 meaning that this way we would need to wait at least 16 reads for an entry to get kicked out. Different cache layers may have different associativity. Most CPU caches are set-associative, unless we are talking about small specialized ones that only house 64 or less entries and can get by with fully-associative schemes.

If we implemented cache in software, we would compute some hash function to use as key. In hardware, we can't really do that because e. g. for L1 cache 4 or 5 cycles is all we got, and even taking a modulo takes 10-15 cycles, let alone something cryptographically secure. Therefore, hardware takes a different approach and calculates this address based on the address. It takes the address, and reinterprets it in three parts:

![](../img/address.png)

The last part is used for determining the cache line it is mapped to. All addresses with the same "middle" part will therefore map to the same set.

Now, where were we? Oh yes, the reason why iterating with strides of 256 has such a terrible slowdown. This because they all map to the same set, and effectively the size of the cache (and all below it) shrinks by 256/16=16. No longer being able to reside in L2, it spills all the way to the order-of-magnitude slower RAM, which causes the expected slowdown.

This issue arises with remarkable frequency in all types of algorithms that love powers of two. Luckily, this behavior is more of an anomaly than some that needs to be dealt with. The solution is usually simple: avoid iterating in powers of two, using different sizer on 2d arrays or inserting "holes" in the memory layout.

Inside these sets, cache operates simply as LRU. Instead of storing time, you just store counters: the later an element was accessed, the lower its counter is. In hardware, you need to maintain $n$ counters of $\log_2 n$ bits each. When a cell is accessed, its counter becomes $(n-1)$ (maximum possible), and the others that are larger need to be decremented by one. Then to kick out an element you need to find the counter with zero and replace it, and then decrement everyone else's counters.

Cost is you need to store more of them (1 more bit per element), and that you need more energy to update all of them. So the practical trade-off is to limit these groups.
