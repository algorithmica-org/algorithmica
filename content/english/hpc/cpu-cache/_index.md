---
title: RAM & CPU Caches
weight: 9
---

In the [previous chapter](../external-memory), we studied computer memory from a theoretical standpoint, using the [external memory model](../external-memory/model) to estimate the performance of memory-bound algorithms.

While the external memory model is more or less accurate for computations involving HDDs and network storage, where cost of arithmetic operations on in-memory values is negligible compared to external I/O operations, it is too imprecise for lower levels in the cache hierarchy, where the costs of these operations become comparable.

To perform more fine-grained optimization of in-memory algorithms, we have to start taking into account the many specific details of the CPU cache system. And instead of studying loads of boring Intel documents with dry specs and theoretically achievable limits, we will estimate these parameters experimentally by running numerous small benchmark programs with access patterns that resemble the ones that often occur in practical code.


<!--

At this level, we can no longer simply ignore either all arithmetic or memory operations. To perform more fine-grained optimization of realistic programs, we need to know the cost of memory accesses on real systems and in real units — in cycles and nanoseconds — along with many other intricacies of the RAM and CPU cache system.

-->

### Experimental Setup

As before, I will be running all experiments on Ryzen 7 4700U, which is a "Zen 2" CPU with the following main cache-related specs:

- 8 physical cores (without hyper-threading) clocked at 2GHz (and 4.1GHz in boost mode — [which we disable](/hpc/profiling/noise));
- 256K of 8-way set associative L1 data cache or 32K per core;
- 4M of 8-way set associative L2 cache or 512K per core;
- 8M of 16-way set associative L3 cache, [shared](sharing) between 8 cores;
- 16GB (2x8G) of DDR4 RAM @ 2667MHz.

You can compare it with your own hardware by running `dmidecode -t cache` or `lshw -class memory` on Linux or by installing [CPU-Z](https://en.wikipedia.org/wiki/CPU-Z) on Windows. You can also find additional details about the CPU on [WikiChip](https://en.wikichip.org/wiki/amd/ryzen_7/4700u) and [7-CPU](https://www.7-cpu.com/cpu/Zen2.html). Not all conclusions will generalize to every CPU platform in existence.

<!--

Although the CPU can be clocked at 4.1GHz in boost mode, we will perform most experiments at 2GHz to reduce noise — so keep in mind that in realistic applications the numbers can be multiplied by 2.

-->

Due to difficulties in [preventing the compiler from optimizing away unused values](/hpc/profiling/noise/), the code snippets in this article are slightly simplified for exposition purposes. Check the [code repository](https://github.com/sslotin/amh-code/tree/main/cpu-cache) if you want to reproduce them yourself.

### Acknowledgements

This chapter is inspired by "[Gallery of Processor Cache Effects](http://igoro.com/archive/gallery-of-processor-cache-effects/)" by Igor Ostrovsky and "[What Every Programmer Should Know About Memory](https://people.freebsd.org/~lstewart/articles/cpumemory.pdf)" by Ulrich Drepper, both of which can serve as good accompanying readings.

<!--

### Recall: CPU Caches

If you jumped to this page straight from Google or just forgot what [we've been doing](../), here is a brief summary of how memory operations work in CPUs:

The last few points may be a bit hand-wavy, but don't worry: they will become clear as we go along with the experiments and demonstrate it all in action.

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

More fundamental [academic paper](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1993/CSD-93-767.pdf) by Rafael Saavedra and Alan Smith.

-->
