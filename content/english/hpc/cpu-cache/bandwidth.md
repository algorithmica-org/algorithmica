---
title: Memory Bandwidth
weight: 1
published: true
---

On the data path between the CPU registers and the RAM, there is a hierarchy of *caches* that exist to speed up access to frequently used data: the layers closer to the processor are faster but also smaller in size. The word "faster" here applies to two closely related but separate timings:

- The delay between the moment when a read or a write is initiated and when the data arrives (*latency*).
- The number of memory operations that can be processed per unit of time (*bandwidth*).

For many algorithms, memory bandwidth is the most important characteristic of the cache system. And at the same time, it is also the easiest to measure, so we are going to start with it.

For our experiment, we create an array and iterate over it $K$ times, incrementing its values:

```cpp
int a[N];

for (int t = 0; t < K; t++)
    for (int i = 0; i < N; i++)
        a[i]++;
```

Changing $N$ and adjusting $K$ so that the total number of array cells accessed remains roughly constant and expressing the total time in "operations per second," we get a graph like this:

![Dotted vertical lines are cache layer sizes](../img/inc.svg)

You can clearly see the cache sizes on this graph:

- When the whole array fits into the lowest layer of cache, the program is bottlenecked by the CPU rather than the L1 cache bandwidth. As the array becomes larger, the overhead associated with the first iterations of the loop becomes smaller, and the performance gets closer to its theoretical maximum of 16 GFLOPS.
- But then the performance drops: first to 12-13 GFLOPS when it exceeds the L1 cache, and then gradually to about 2 GFLOPS when it can no longer fit in the L3 cache.

This situation is typical for many lightweight loops.

### Frequency Scaling

All CPU cache layers are placed on the same microchip as the processor, so the bandwidth, latency, and all its other characteristics scale with the clock frequency. The RAM, on the other side, lives on its own fixed clock, and its characteristics remain constant. We can observe this by re-running the same benchmarking with turbo boost on:

![](../img/boost.svg)

This detail comes into play when comparing algorithm implementations. When the working dataset fits in the cache, the relative performance of the two implementations may be different depending on the CPU clock rate because the RAM remains unaffected by it (while everything else does not).

For this reason, it is [advised](/hpc/profiling/noise) to keep the clock rate fixed, and as the turbo boost isn't stable enough, we run most of the benchmarks in this book at plain 2GHz.

### Directional Access

This incrementing loop needs to perform both reads and writes during its execution: on each iteration, we fetch a value, increment it, and then write it back. In many applications, we only need to do one of them, so let’s try to measure unidirectional bandwidth.

Calculating the sum of an array only requires memory reads:

```c++
for (int i = 0; i < N; i++)
    s += a[i];
```

And zeroing an array (or filling it with any other constant value) only requires memory writes:

```c++
for (int i = 0; i < N; i++)
    a[i] = 0;
```

Both loops are trivially [vectorized](/hpc/simd) by the compiler, and the second one is actually replaced with a `memset`, so the CPU is also not the bottleneck here (except when the array fits into the L1 cache).

![](../img/directional.svg)

The reason why unidirectional and bidirectional memory accesses would perform differently is that they share the cache and memory buses and other CPU facilities. In the case of RAM, this causes a twofold difference in performance between the pure read and simultaneous read and write scenarios because the memory controller has to switch between the modes on the one-way memory bus, thus halving the bandwidth. The performance drop is less severe for the L2 cache: the bottleneck here is not the cache bus, so the incrementing loop loses by only ~15%.

There is one interesting anomaly on the graph, namely that the write-only loop performs the same as the read-and-write one when the array hits the L3 cache and the RAM. This is because the CPU moves the data to the highest level of cache on each access, whether it is a read or a write — which is typically a good optimization, as in many use cases we will be needing it soon. When reading data, this isn't a problem, as the data travels through the cache hierarchy anyway, but when writing, this causes another implicit read to be dispatched right after a write — thus requiring twice the bus bandwidth.

### Bypassing the Cache

We can prevent the CPU from prefetching the data that we just have written by using *non-temporal* memory accesses. To do this, we need to re-implement the zeroing loop more directly without relying on compiler vectorization.

Ignoring a few special cases, what `memset` and auto-vectorized assignment loops do under the hood is they just [move](/hpc/simd/moving) 32-byte blocks of data with [SIMD instructions](/hpc/simd):

```c++
const __m256i zeros = _mm256_set1_epi32(0);

for (int i = 0; i + 7 < N; i += 8)
    _mm256_store_si256((__m256i*) &a[i], zeros);
```

We can replace the usual vector store intrinsic with a *non-temporal* one:

```c++
const __m256i zeros = _mm256_set1_epi32(0);

for (int i = 0; i + 7 < N; i += 8)
    _mm256_stream_si256((__m256i*) &a[i], zeros);
```

Non-temporal memory reads or writes are a way to tell the CPU that we won't be needing the data that we have just accessed in the future, so there is no need to read the data back after a write.

![](../img/non-temporal.svg)

On the one hand, if the array is small enough to fit into the cache, and we actually access it some short time after, this has a negative effect because we have to read entirely it from the RAM (or, in this case, we have to *write* it into the RAM instead of using a locally cached version). And on the other, this prevents read-backs and lets us use the memory bus more efficiently.

In fact, the performance increase in the case of the RAM is even more than 2x and faster than the read-only benchmark. This happens because:

- the memory controller doesn't have to switch the bus between read and write modes this way;
- the instruction sequence becomes simpler, allowing for more pending memory instructions;
- and, most importantly, the memory controller can simply "fire and forget" non-temporal write requests — while for reads, it needs to remember what to do with the data once it arrives (similar to connection handles in networking software).

Theoretically, both requests should use the same bandwidth: a read request sends an address and gets data, and a non-temporal write request sends an address *with* data and gets nothing. Not accounting for the direction, we transmit the same data, but the read cycle will be longer because it needs to wait for the data to be fetched. Since [there is a practical limit](../mlp) on how many concurrent requests the memory system can handle, this difference in read/write cycle latency also results in the difference in their bandwidth.

Also, for these reasons, a single CPU core usually [can't fully saturate the memory bandwidth](../sharing).

The same technique generalizes to `memcpy`: it also just moves 32-byte blocks with SIMD load/store instructions, and it can be similarly made non-temporal, increasing the throughput twofold for large arrays. There is also a non-temporal load instruction (`_mm256_stream_load_si256`) for when you want to *read* without polluting cache (e.g., when you don't need the original array after a `memcpy`, but will need some data that you had accessed before calling it).
