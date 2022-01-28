---
title: Memory Bandwidth
weight: 1
---

On the data path between the CPU registers and the RAM, there is a hierarchy of *caches* that exist to speed up access to frequently used data: the layers closer to the processor are are faster, but also smaller in size. The word "faster" here means two things:

- The time between the moment when a read (or write) is initiated and the moment when it is (latency).
- The number of 

- Caching is done transparently; when there isn't enough space to fit a new cache line, the least recently used one automatically gets evicted to the next, slower layer of cache hierarchy. The programmer can't control this process explicitly.

-->

For many algorithms, *memory bandwidth* is the most important characteristic of the cache system. And at the same time, it is also the easiest to measure.

For our experiment, we create an array and iterate over it $K$ times incrementing its values:

```cpp
int a[N];

for (int t = 0; t < K; t++)
    for (int i = 0; i < N; i++)
        a[i]++;
```

Changing $N$ and adjusting $K$ so that the total number of cells accessed remains roughly constant, and normalizing the timings as "operations per second", we get the following results:

![Dotted vertical lines are cache layer sizes](../img/inc.svg)

You can clearly see the sizes of the cache layers on this graph. When the whole array fits into the lowest layer of cache, the program is bottlenecked by CPU rather than L1 cache bandwidth. As the the array becomes larger, overhead becomes smaller, and the performance approaches this theoretical maximum. But then it drops: first to ~12 GFLOPS when it exceeds L1 cache, and then gradually to about 2.1 GFLOPS when it can no longer fit in L3.

### Directional Access

Only read:

```c++
for (int i = 0; i < N; i++)
    s += a[i];
```

Only write:

```c++
// same as memset(a, 0, sizeof a);
for (int i = 0; i < N; i++)
    a[i] = 0;
```

![](../img/directional.svg)

### Frequency Scaling

All CPU cache layers are placed on the same microchip as the processor, so bandwidth, latency, all its other characteristics scale with the clock frequency. RAM, on the other side, lives on its own clock, and its characteristics remain constant. This can be seen on these graphs if we run the same benchmark while turning frequency boost on:

![](../img/boost.svg)

To reduce noise, we will run all the remaining benchmarks at plain 2GHz — but the lesson to retain here is that the relative performance of different approaches or decisions between algorithm designs may depend on the clock frequency — unless when we are working with datasets that either fit in cache entirely.

Caches are physically a part of CPU. Accessing them takes a fixed amount of time in CPU cycles, so their real access time is proportional to the clock rate. On the contrary, RAM is a separate chip with its own clock rate. Its latencies are therefore better measured in nanoseconds, and not cycles.
