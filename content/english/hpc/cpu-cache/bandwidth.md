---
title: Memory Bandwidth
weight: 1
---

For many algorithms, memory bandwidth is the most important characteristic of the cache system. Coincidentally, it is also the easiest to measure.

For our benchmark, let's create an array and linearly iterate over it $K$ times, incrementing its values:

```cpp
int a[N];

for (int t = 0; t < K; t++)
    for (int i = 0; i < N; i++)
        a[i]++;
```

Changing $N$ and adjusting $K$ so that the total number of cells accessed remains roughly constant, and normalizing the timings as "operations per second", we get the following results:

![Dotted vertical lines are cache layer sizes](../img/inc.svg)

You can clearly see the sizes of the cache layers on this graph. When the whole array fits into the lowest layer of cache, the program is bottlenecked by CPU rather than L1 cache bandwidth. As the the array becomes larger, overhead becomes smaller, and the performance approaches this theoretical maximum. But then it drops: first to ~12 GFLOPS when it exceeds L1 cache, and then gradually to about 2.1 GFLOPS when it can no longer fit in L3.

All CPU cache layers are placed on the same microchip as the processor, so bandwidth, latency, all its other characteristics scale with the clock frequency. RAM, on the other side, lives on its own clock, and its characteristics remain constant. This can be seen on these graphs if we run the same benchmark while turning frequency boost on:

![](../img/boost.svg)

To reduce noise, we will run all the remaining benchmarks at plain 2GHz — but the lesson to retain here is that the relative performance of different approaches or decisions between algorithm designs may depend on the clock frequency — unless when we are working with datasets that either fit in cache entirely.

<!-- TODO: measure frequency-boosted latency also and move to a separate section -->

**Exercise: theoretical peak performance.** By the way, assuming infinite bandwidth, what would the throughput of that loop be? How to verify that the 14 GFLOPS figure is the CPU limit and not L1 peak bandwidth? For that we need to look a bit closer at how the processor will execute the loop.

Incrementing an array can be done with SIMD; when compiled, it uses just two operations per 8 elements — performing the read-fused addition and writing the result back:

```asm
vpaddd  ymm0, ymm1, YMMWORD PTR [rax]
vmovdqa YMMWORD PTR [rax], ymm0
```

This computation is bottlenecked by the write, which has a throughput of 1. This means that we can theoretically increment and write back 8 values per cycle on average, yielding the performance of 2 GHz × 8 = 16 GFLOPS (or 32.8 in boost mode), which is fairly close to what we observed.

On all modern architectures, you can typically assume that you won't ever be bottlenecked by the throughput of L1 cache, but rather by the read/write execution ports or the arithmetic. In these extreme cases, it may be beneficial to store some data in registers without touching any of the memory, which we will cover later in the book.
