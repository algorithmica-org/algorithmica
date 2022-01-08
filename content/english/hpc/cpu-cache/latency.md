---
title: Memory Latency
weight: 1
---

Despite bandwidth — how many data one can load — is a more complicated concept, it is much easier to observe and measure than latency — how much time it takes to load one cache line.

Measuring memory bandwidth is easy because the CPU can simply queue up multiple iterations of data-parallel loops like the one above. The scheduler gets access to the needed memory locations far in advance and can dispatch read requests in a way that will overlap all memory operations, hiding the latency.

To measure latency, we need to design an experiment where the CPU can't cheat by knowing the memory location in advance. We can do this like this: generate a random permutation of size $n$ that corresponds a full cycle, and then repeatedly follow the permutation.

```cpp
int p[N], q[N];

iota(p, p + N, 0);
random_shuffle(p, p + N);

int k = p[N - 1];
for (int i = 0; i < N; i++)
    k = q[k] = p[i];

for (int t = 0; t < K; t++)
    for (int i = 0; i < N; i++)
        k = q[k];
```

This performance anti-pattern is known as *pointer chasing*, and it very frequent in software, especially written in high-level languages. Iterating an array this way is considerably slower.

![](../img/permutation-latency.svg)

When speaking of latency, it makes more sense to use cycles or nanoseconds rather than bandwidth units. So we will replace this graph with its reciprocal:

![](../img/latency-throughput.svg)

It is generally *much* slower — by multiple orders of magnitude — to iterate an array this way. Not only because it makes SIMD practically impossible, but also because it stalls the pipeline a lot.

### Latency of RAM and TLB

Similar to bandwidth, the latency of CPU cache scales with its clock frequency, while the RAM lives on its own fixed-frequency clock, and its performance is therefore usually measured in nanoseconds. We can observe this difference if we change the frequency by turning turbo boost on.

![](../img/permutation-boost.svg)

The graph starts making a bit more sense if we look at the relative speedup instead.

![](../img/permutation-boost-speedup.svg)

You would expect 2x rates for array sizes that fit into CPU cache entirely, but then roughly equal for arrays stored in RAM. But this is not quite what is happening: there is a small, fixed-latency delay on lower clocked run even for RAM accesses. This happens because the CPU first checks its cache before dispatching a read query to the main memory — to save RAM bandwidth for other processes that potentially need it.

Actually, TLB misses may stall memory reads for the same reason. The TLB cache is called "lookaside" because the lookup can happen independently from normal data cache lookups. L1 and L2 caches on the other side are private to the core, and so they can store virtual addresses and be queried concurrently with TLB — after fetching a cache line, its tag is used to restore the physical address, which is then checked against the concurrently fetched TLB entry. This trick does not work for shared memory however, because their bandwidth is limited, and dispatching read queries there for no reason is not a good idea in general. So we can observe a similar effect in L3 and RAM reads when the page does not fit L1 TLB and L2 TLB respectively.

For sparse reads, it often makes sense to increase page size, which improves the latency.

It is possible, but quite tedious to also construct an experiment actually measuring all this — so you will have to take my word on that one.
