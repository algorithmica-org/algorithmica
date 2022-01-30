---
title: Cache Lines
weight: 3
---

- The CPU cache system operates on *cache lines*, which is the basic unit of data transfer between the CPU and the RAM. The size of a cache line is 64 bytes on most architectures, meaning that all main memory is divided into blocks of 64 bytes, and whenever you request (read or write) a single byte, you are also fetching all its 63 cache line neighbors whether your want them or not.


The most important feature of the memory system is that it deals with cache lines, and not individual bytes.

To demonstrate this, let's add "step" parameter to our loop — we will now increment every $D$-th element:
 
```cpp
for (int t = 0; t < K; t++)
    for (int i = 0; i < N; i += D)
        a[i]++;
```

When we run it with $D=16$, we can observe something interesting:

![Performance is normalized by the total time to run benchmark, not the total number of elements incremented](../img/strided.svg)

As the problem size grows, the graphs of the two loops meet, despite one doing 16 times less work than the other. This is because in terms of cache lines, we are fetching exactly the same memory; the fact that the strided computation only needs one sixteenth of it is irrelevant.

It does work a bit faster when the array fits into lower layers of cache because the loop becomes much simples: all it does is `inc DWORD PTR [rdx]` (yes, x86 has instructions that only involve memory locations and no registers or immediate values). It also has a throughput of one, but while the former code needed to perform two of writes per cache line, this only needs one, hence it works twice as fast when memory is not a concern.

When we change the step parameter to 8, the graphs equalize:

![](../img/strided2.svg)

The important lesson is to count the number of cache lines to fetch when analyzing memory-bound algorithms, and not the total count of memory accesses. This becomes increasingly important with larger problem sizes.

![](../img/permutation-padded.svg)

### Other Blocks

Pages

RAM rows. 3-4 nanosecond increase.


<!--

Actually, TLB misses may stall memory reads for the same reason. The TLB cache is called "lookaside" because the lookup can happen independently from normal data cache lookups. L1 and L2 caches on the other side are private to the core, and so they can store virtual addresses and be queried concurrently with TLB — after fetching a cache line, its tag is used to restore the physical address, which is then checked against the concurrently fetched TLB entry. This trick does not work for shared memory however, because their bandwidth is limited, and dispatching read queries there for no reason is not a good idea in general. So we can observe a similar effect in L3 and RAM reads when the page does not fit L1 TLB and L2 TLB respectively.

For sparse reads, it often makes sense to increase page size, which improves the latency.

It is possible, but quite tedious to also construct an experiment actually measuring all this — so you will have to take my word on that one.

-->

