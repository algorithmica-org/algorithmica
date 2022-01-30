---
title: Memory Latency
weight: 2
---

Despite that [bandwidth](../bandwidth) is a more complicated concept, it is much easier to observe and measure than latency: you can simply execute a long series of independent read or write queries, and the scheduler, having access to them in advance, reorders and overlaps them, hiding their latency and maximizing the total throughput.

To measure *latency*, we need to design an experiment where the CPU can't cheat by knowing the memory locations we are going to request in advance. One way to ensure this is to generate a random permutation of size $N$ that corresponds to a full cycle, and then repeatedly follow the permutation:

```cpp
int p[N], q[N];

// generating a random permutation
iota(p, p + N, 0);
random_shuffle(p, p + N);

// this permutation may contain multiple cycles,
// so instead we use it to construct another permutation with a single cycle
int k = p[N - 1];
for (int i = 0; i < N; i++)
    k = q[k] = p[i];

for (int t = 0; t < K; t++)
    for (int i = 0; i < N; i++)
        k = q[k];
```

Compared to linear iteration, it is *much* slower — by multiple orders of magnitude — to visit all elements of an array this way. Not only does it make [SIMD](/hpc/simd) impossible, but it also [stalls the pipeline](/hpc/pipelining), creating a large traffic jam of instructions, all waiting for a single piece of data to be fetched from the memory.

This performance anti-pattern is known as *pointer chasing*, and it is very frequent in data structures, especially those written high-level languages that use lots of heap-allocated objects and pointers to them necessary for dynamic typing.

![](../img/latency-throughput.svg)

When talking about latency, it makes more sense to use cycles or nanoseconds rather than throughput units. So we will replace this graph with its reciprocal:

![](../img/permutation-latency.svg)

Note that the cliffs on both graphs aren't as distinctive as they were for the bandwidth. This is because we still have some chance of hitting the previous layer of cache even if the array can't fit into it entirely. More formally, there are $k$ levels in the cache hierarchy with sizes $s_i$ and latencies $l_i$, then their expected latency will be

$$
E[L] = \frac{
      s_1 \cdot l_1
    + (s_2 - s_1) \cdot l_2
%    + (s_3 - s_2) \cdot l_3
    + \ldots
    + (N - s_k) \cdot l_{RAM}
    }{N}
$$

instead of just being equal to the slowest access.

Since sizes and latencies typically differ by almost an order of magnitude. When we increase the size of the array. So the graph of reciprocal latency should roughly look like if it was composed of a few transposed and scaled hyperbolas.

we aren't exactly measuring latency in this experiment.

$$
E[L] = \frac{N \cdot l_{last} - C}{N} = l_{last} - \frac{C}{N}
$$

$$
\frac{1}{l_{last} - \frac{C}{N}}
= \frac{N}{N \cdot l_{last} - C}
$$

<!--

E[L] \approx \frac{s_{k} \cdot l_{k} + (N - s_k) \cdot l_{k+1}}{N}
= l_{k+1} - \frac{s_k \cdot (l_{k+1} - l_k)}{N} 

-->

### Frequency Scaling

Similar to bandwidth, the latency of all CPU caches proportionally scales with its clock frequency, while the RAM does not. We can also observe this difference if we change the frequency by turning turbo boost on.

![](../img/permutation-boost.svg)

The graph starts making a more sense if we plot it as a relative speedup.

![](../img/permutation-boost-speedup.svg)

You would expect 2x rates for array sizes that fit into CPU cache entirely, but then roughly equal for arrays stored in RAM. But this is not quite what is happening: there is a small, fixed-latency delay on lower clocked run even for RAM accesses. This happens because the CPU first has to check its cache before dispatching a read query to the main memory — to save RAM bandwidth for other processes that potentially need it.
