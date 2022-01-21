---
title: RAM & CPU Caches
weight: 9
---

In the previous chapter, we studied computer memory from theoretical standpoint, using the [external memory model](../external-memory) to estimate performance of memory-bound algorithms.

While it is more or less accurate for computations involving HDDs and network storage, where in-memory arithmetic is negligibly fast compared to external I/O operations, it becomes erroneous on lower levels in the cache hierarchy, where the costs of these operations become comparable.

At this level, we can no longer simply ignore either all arithmetic or memory operations. To perform more fine-grained optimization of realistic programs, we need to know the cost of memory accesses on real systems and in real units — in cycles and nanoseconds — along with many other intricacies of the RAM and CPU cache system.

To do so, instead of digging ourselves in Intel spec sheets filled with theoretically possible performance metrics, we will estimate these parameters experimentally: by running small benchmark programs that perform access patterns that may realistically occur in real code.

### Recall: CPU Caches

If you jumped to this page straight from Google or just forgot what [we've been doing](../), here is a brief summary of how memory operations work in CPUs:

- In-between CPU registers and RAM, there is a hierarchy of *caches* that exist to speed up access to frequently used data: "lower" layers are faster, but more expensive and therefore smaller in size.
- Caches are physically a part of CPU. Accessing them takes a fixed amount of time in CPU cycles, so their real access time is proportional to the clock rate. On the contrary, RAM is a separate chip with its own clock rate. Its latencies are therefore better measured in nanoseconds, and not cycles.
- The CPU cache system operates on *cache lines*, which is the basic unit of data transfer between the CPU and the RAM. The size of a cache line is 64 bytes on most architectures, meaning that all main memory is divided into blocks of 64 bytes, and whenever you request (read or write) a single byte, you are also fetching all its 63 cache line neighbors whether your want them or not.
- Memory requests can overlap in time: while you wait for a read request to complete, you can sand a few others, which will be executed concurrently. In some contexts that allow for many concurrent I/O operations it therefore makes more sense to talk abound memory *bandwidth* than *latency*.
- Taking advantage of this free concurrency, it is often beneficial to *prefetch* data that you will likely be accessing soon, if you know its location. You can do this explicitly by using a separate instruction or just by accessing any byte in its cache line, but the most frequent patterns, such as linearly iterating forward or backward over an array, prefetching is already handled by hardware.
- Caching is done transparently; when there isn't enough space to fit a new cache line, the least recently used one automatically gets evicted to the next, slower layer of cache hierarchy. The programmer can't control this process explicitly.
- Since implementing "find the oldest among million cache lines" in hardware is unfeasible, each cache layer is split in a number of small "sets", each covering a certain subset of memory locations. *Associativity* is the size of these sets, or, in other terms, how many different "cells" of cache each data location can be mapped to. Higher associativity allows more efficient utilization of cache.
- There are other types of cache inside CPUs that are used for things other than data. The most important for us are *instruction cache* (I-cache), which is used to speed up the fetching of machine code from memory, and *translation lookaside buffer* (TLB), which is used to store physical locations of virtual memory pages, which is instrumental to the efficiency of virtual memory.

The last few points may be a bit hand-wavy, but don't worry: they will become clear as we go along with the experiments and demonstrate it all in action.

**Setup.** As before, I will be running these experiments on [Ryzen 7 4700U](https://en.wikichip.org/wiki/amd/ryzen_7/4700u), which is a "Zen 2" CPU whose cache-related specs are as follows:

- 8 physical cores (without hyper-threading) clocked at 2GHz[^boost];
- 512K of 8-way set associative L1 cache, half of which is instruction cache — meaning 32K per core;
- 4M of 8-way set associative L2 cache, or 512K per core;
- 8M of 16-way set associative L3 cache, *shared* between 8 cores (4M actually);
- 16G of DDR4 RAM @ 2667MHz.

[^boost]: Although the CPU can be clocked at 4.1GHz in boost mode, we will perform most experiments at 2GHz to reduce noise — so keep in mind that in realistic applications the numbers can be multiplied by 2.

You can compare it with your own hardware by running `dmidecode -t cache` or `lshw -class memory` on Linux or just looking it up on WikiChip.

Due to difficulties in [refraining compiler from cheating](..//hpc/analyzing-performance/profiling/), the code snippets in this article are be slightly simplified for exposition purposes. Check the [code repository](https://github.com/sslotin/amh-code/tree/main/cpu-cache) if you want to reproduce them yourself.

I am not going to turn off frequency boosting or silence other programs while doing these benchmarks. The goal is to get realistic values, like when optimizing a video game.


## Summary and Lessons Learned

Excluding TLB, our experiments suggest the following:

| Type | Size | Latency | Bandwidth |
|:-----|:-----|---------|-----------|
| L1   | 32K  | 2ns     | $\infty$  |
| L2   | 512K | 10ns    | 50G/s     |
| L3   | 4M   | 50ns    | 35G/s     |
| RAM  | GB   | 100ns   | 8G/s      |

There are more thorough [measurements for Zen 2](https://www.7-cpu.com/cpu/Zen2.html).

We can learn valuable lessons from our experiments. There are two types of memory-bound algorithms. Loops or data structures.

**Latency-constrained.** For the purpose of designing algorithms, a more important characteristic is the **bandwidth-latency product** which basically tells how many cache lines you can request while waiting for the first one without queueing up. It is around 5 or more on most systems. CPUs can detect simple patterns such as linear iteration forward or backward.

**Bandwidth-constrained.** We started the previous section with how it is not relevant which algorithm is used to determine cache eviction. In most practical cases, this is really the case.

But in some cases the specifics start to matter. In set-associative cache, there may be a problem when we are only working with data cells that all map to the same cache line. When is this the case? When we are considering memory locations that are all have the same remainder modulo some large power of two.

Unfortunately, this happens quite often, as we programmers love using powers of two for our algorithms and data structures.

Fortunately, this is easy to fix: just don't use powers of two. Not necessarily for the algorithm, but at least for the memory layout.

## Further Reading

This article is inspired by "[Gallery of Processor Cache Effects](http://igoro.com/archive/gallery-of-processor-cache-effects/)" by Igor Ostrovsky.

For a more a comprehensive read, consider "[What Every Programmer Should Know About Memory](https://people.freebsd.org/~lstewart/articles/cpumemory.pdf)" by Ulrich Drepper.

More fundamental [academic paper](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1993/CSD-93-767.pdf) by Rafael Saavedra and Alan Smith.
