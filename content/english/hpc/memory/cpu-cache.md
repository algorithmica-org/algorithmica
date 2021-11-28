---
title: RAM & CPU Caches
weight: 4
draft: true
---

Previously in this chapter, we studied computer memory from theoretical standpoint, using the [external memory model](../external-memory) to estimate performance of memory-bound algorithms.

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

- 8 physical cores (without hyper-threading), clocked at 4.1GHz in boost mode;
- 512K of 8-way set associative L1 cache, half of which is instruction cache — meaning 32K per core;
- 4M of 8-way set associative L2 cache, or 512K per core;
- 8M of 16-way set associative L3 cache, *shared* between 8 cores (4M actually);
- 16G of DDR4 RAM @ 2667MHz.

You can compare it with your own hardware by running `dmidecode -t cache` or `lshw -class memory` on Linux or just looking it up on WikiChip.

Due to difficulties in [refraining compiler from cheating](http://localhost:1313/hpc/analyzing-performance/profiling/), the code snippets in this article are be slightly simplified for exposition purposes. Check the [code repository](https://github.com/sslotin/amh-code/tree/main/cpu-cache) if you want to reproduce them yourself.

I am not going to turn off frequency boosting or silence other programs while doing these benchmarks. The goal is to get realistic values, like when optimizing a video game.

## Memory Bandwidth

For many algorithms, memory bandwidth is the most important characteristic of the cache system. Coincidentally, it is also the easiest to measure.

Let's create an array and linearly iterate over it $K$ times, incrementing its values:

```cpp
int a[N];

for (int t = 0; t < K; t++)
    for (int i = 0; i < N; i++)
        a[i]++;
```

Changing $N$, adjusting $K$ so that the total number of cells accessed remains roughly constant, and normalizing timings as "operations per second", we get the following results:

![Dotted vertical lines are cache layer sizes](../img/inc.svg)

When the whole array fits into the lowest layer of cache, the program is bottlenecked by CPU rather than L1 cache bandwidth. Incrementing an array can be done with SIMD; compiled it uses just two operations per 8 elements — performing the read-fused addition and writing the result back:

```asm
vpaddd  ymm0, ymm1, YMMWORD PTR [rax]
vmovdqa YMMWORD PTR [rax], ymm0
```

This computation is bottlenecked by the write, which has a throughput of 1. This means that we can theoretically increment and write back 8 values per cycle on average, yielding the performance of 4.1 GHz × 8 = 32.8 GFLOPS.

As the the array becomes larger, overhead becomes smaller, and the performance approaches this theoretical maximum. But then it drops: first to 25 GFLOPS when it exceeds L1 cache, and then gradually to about 2.1 GFLOPS when it can no longer fit in L3.

### Parallel Execution

The last cliff is not sharp because of noisy neighbors. L1 and L2 caches are private to the core, but L3 is shared. When a single program accesses a cache line, it causes the whole thing to stall, hence the performance penalty.

![Cache hierarchy in Zen 2](../img/zen2.png)

Bandwidth at this level is shared.

Another factor is that it is that the clock frequency is boosted. We can set it at sustainable level, and it flattens out.

### Cache Lines

One unignorable feature of the memory system is that it deals with cache lines, and not individual bytes.

To demonstrate this, we will add "step" parameter to our loop — we will now increment every $D$-th element:

```cpp
for (int t = 0; t < K; t++)
    for (int i = 0; i < N; i += D)
        a[i]++;
```

When we run it with $D=16$, we can observe something interesting:

![Blue line is every 16 elements](../img/strided.svg)

As the problem size grows, the two lines meet, despite one doing 16 times less work than the other. This is because in terms of cache lines, we are fetching exactly the same memory; the fact that the strided computation only needs one sixteenth of it is irrelevant.

That said, it does work a bit faster when the array fits in L1. This is because all it does is `inc DWORD PTR [rdx]` (yes, x86 has instructions that only involve memory locations and no registers or immediate values). It also has a throughput of 1, but while the former code needed 2 of writes per cache line, this only needs one, hence it works twice as fast when memory is not a concern.

When we change the step parameter to 8, the graphs equalize:

![](../img/strided2.svg)

Important lesson is to count the number of cache lines to fetch, and not the total count of memory accesses, especially when working with large problems. 

### Cache Associativity

Let's try a few other, larger strides. Since strides larger than 16 will "skip" some cache lines altogether, we normalize the running time in terms of total number of values incremented, and also adjust the array size so that the loop always does a roughly constant number of iterations and reads constant number of cache lines.

IMAGE HERE

What are the spikes there? These correspond to step sizes that are either powers of two, or divisible by large powers of two. This is due to a feature called *cache associativity*, and an interesting artifact of how CPU caches are implemented in hardware.

Here is the gist of it.

![Fully associative cache](../img/cache2.png)

Implementing something like that is prohibitively expensive.

The simplest way to implement cache is to map each block of 64 bytes in RAM to a cache line which it can possibly occupy. Say if in we have 4096 blocks in memory and 64 cache lines for them, this means that each cache line at any time stores the value of one of $\frac{4096}{64} = 64$ different blocks, along with a "tag" information which helps identifying which block it is.

![Direct-mapped cache](../img/cache1.png)

The simplest way to do this is to take address, and to reinterpret it in three parts:

The way it happens is an address is split into three parts, the last of which is used for determining the cache line it is mapped to.

![](../img/address.png)

Therefore, every

For that, we settle for something in-between direct-mapped and fully associative cache: the *set-associative cache*.

![Set-associative cache](../img/cache3.png)

Different cache layers may have different associativity.

### Paging and TLB

It is "lookaside" is because it is looked up concurrently with the accesses in the cache. First layer typically uses virtual addresses anyway. Memory controller retrieves entries in cache and TLB, and then compares the tag.

Paging is implemented both on software (OS) and hardware level.

Typical size of a page is 4KB,

TLB cache which is used for storing.

### Implications in Algorithm Design

We started the previous section with how it is not relevant which algorithm is used to determine cache eviction. In most practical cases, this is really the case.

But in some cases the specifics start to matter. In set-associative cache, there may be a problem when we are only working with data cells that all map to the same cache line. When is this the case? When we are considering memory locations that are all have the same remainder modulo some large power of two.

Unfortunately, this happens quite often, as we programmers love using powers of two for our algorithms and data structures.

Fortunately, this is easy to fix: just don't use powers of two. Not necessarily for the algorithm, but at least for the memory layout.

## Memory Latency

For the purpose of designing algorithms, a more important characteristic is the **bandwidth-latency product** which basically tells how many cache lines you can request while waiting for the first one without queueing up. It is around 5 or more on most systems. CPUs can detect simple patterns such as linear iteration forward or backward.

Permutation.

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

What we do is called *pointer chasing*.

The latency of L1 fetch is 4 or 5 cycles, the latter being the case if we need to use fused computation of address. In theory, it works slightly faster if we are working with actual pointers.

### ILP and Speculative Execution

* CPU: "hey, I'm probably going to wait ~100 more cycles for that memory fetch"
* "why don't I execute some of the later operations in the pipeline ahead of time?"
* "even if they won't be needed, I just discard them"

```cpp
bool cond = some_long_memory_operation();

if (cond)
    do_this_fast_operation();
else
    do_that_fast_operation();
```

*Implicit prefetching*: memory reads can be speculative too, and reads will be pipelined anyway

(By the way, this is what Meltdown was all about)

### Hardware Prefetching

```cpp
int p[15], q[N];

iota(p, p + 15, 1);

for (int i = 0; i + 16 < N; i += 16) {
    random_shuffle(p, p + 15);
    int k = i;
    for (int j = 0; j < 15; j++)
        k = q[k] = i + p[j];
    q[k] = i + 16;
}
```

### Software Prefetching

Sometimes the CPU can't figure it out by itself.

```cpp
const int n = find_prime(N);

for (int i = 0; i < n; i++)
    q[i] = (2 * i + 1) % n;
```

```cpp
int k = 0;

for (int t = 0; t < K; t++) {
    for (int i = 0; i < n; i++) {
        __builtin_prefetch(&q[(2 * k + 1) % n]);
        k = q[k];
    }
}
```

```cpp
__builtin_prefetch(&q[((1 << D) * k + (1 << D) - 1) % n]);
```

## Summary

| Type | $M$      | $B$ | Latency | Bandwidth | $/GB/mo[^pricing] |
|:-----|:---------|-----|---------|-----------|:------------------|
| L1   | 10K      | 64B | 0.5ns   | 80G/s     | -                 |
| L2   | 100K     | 64B | 5ns     | 40G/s     | -                 |
| L3   | 1M/core  | 64B | 20ns    | 20G/s     | -                 |
| RAM  | GBs      | 64B | 100ns   | 10G/s     | 1.5               |
| SSD  | TBs      | 4K  | 0.1ms   | 5G/s      | 0.17              |
| HDD  | TBs      | -   | 10ms    | 1G/s      | 0.04              |
| S3   | $\infty$ | -   | 150ms   | $\infty$  | 0.02[^S3]         |

## Acknowledgements

This article is inspired by "[Gallery of Processor Cache Effects](http://igoro.com/archive/gallery-of-processor-cache-effects/)" by Igor Ostrovsky.

For a more a comprehensive read, consider "[What Every Programmer Should Know About Memory](https://people.freebsd.org/~lstewart/articles/cpumemory.pdf)" by Ulrich Drepper.

More fundamental [academic paper](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1993/CSD-93-767.pdf) by Rafael Saavedra and Alan Smith.
