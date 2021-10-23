---
title: RAM & CPU Caches
weight: 4
draft: true
---

Here is a famous quote about caching:

![](img/cache_and_beer.png)

The reality is much more complicated, e. g. main memory has pagination and HDD is actually a rotating physical thing with weird access patterns, but we stick to this analogy and introduce some important entities to it:

* **Cache hierarchy** is a memory architecture which uses a hierarchy of memory stores based on varying access speeds to cache data. Adjacent cache layers usually differ in size by a factor of 8 to 10 and in latency by a factor of 3 to 5. Most modern CPUs have 3 layers of cache (called L1, L2 and L3 from fastest / smallest to slowest / largest) with largest being a few megabytes large.

* **Cache line** is the unit of data transfer between CPU and main memory. The cache line of your PC is most likely 64 bytes, meaning that the main memory is divided into blocks of 64 bytes, and whenever you request a byte, you are also fetching its cache line neighbours regardless whether your want it or not. *Fetching a cache line is like grabbing a 6-pack.*

* **Eviction policy** is the method for deciding which data to retain in the cache. In CPUs, it is controlled by hardware, not software. For simplicity, programmer can assume that **least recently used (LRU)** policy is used, which just evicts the item that hasn't been used for the longest amount of time. *This is like preferring beer with later expiration dates.*

* **Bandwidth** is the rate at which data can be read or stored. For the purpose of designing algorithms, a more important characteristic is the **bandwidth-latency product** which basically tells how many cache lines you can request while waiting for the first one without queueing up. It is around 5 or more on most systems. *This is like having friends whom you can send for beers asynchronously.*

* **Temporal locality** is an access pattern where if at one point a particular item is requested, it is likely that this same location will be requested again in the near future. *This is like fetching the same type of beer over and over again.*

* **Spacial locality** is an access pattern where if a memory location is requested, it is likely that a nearby memory locations will be requested again in the near future. *This is like storing the kinds of beer that you like on the same shelf.*

---

In previous sections of this chapter, we mostly studied the theoretical side and did a lot of hand waving when it came to real implementations. In this section, we will study the RAM and CPU cache system in higher detail.

We will do so while doing actual measurements.

To recall, we are running [Ryzen 7 4700U](https://en.wikichip.org/wiki/amd/ryzen_7/4700u) @ 4.1GHz. Its specs are as follows:

- 8 physical cores (which is a very rare exception nowadays)
- 512KB or L1 cache, half of which is instruction cache, so effectively 32K per core
- 4MB of L2 cache, or 512K per core
- 8MB of L3 cache, shared between 8 cores
- 16GB of RAM

You can get these stats for your chip by calling `dmidecode -t cache` and `dmidecode -t cache` on Linux or looking it up on WikiChip.

Like in physics, we will try to measure it experimentally.

## Memory Bandwidth

```cpp
for (int t = 0; t < K; t++)
    for (int i = 0; i < N; i += D)
        a[i]++;
```

Compiled with `g++ -O3 -funroll-loops -march=native`

![](../img/inc.svg)

![](../img/strided.svg)

## Memory Latency

Permutation.

Pointer chasing

## Cache Lines

Burst memory.

### Speculative Execution

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

### Prefetching

Sometimes the CPU can't figure it out by itself.

Let's try to measure.

## Cache Associativity

There are a few ways to do caching. For simplicity, we will consider L3-RAM boundary, but the reasoning for every other level is exactly the same.

The simplest is to map each RAM cell.

![Direct-mapped cache](../img/cache1.png)

![Fully associative cache](../img/cache2.png)

Implementing something like that is prohibitively expensive. For that, we settle for something in-between direct-mapped and fully associative cache: the *set-associative cache*.

![Set-associative cache](../img/cache3.png)

Different cache layers usually have different associativity.

The way it happens is an address is split into three parts, the last of which is used for determining the cache line it is mapped to.

### So What?

We started the previous section with how it is not relevant which algorithm is used to determine cache eviction. In most practical cases, this is really the case.

But in some cases the specifics start to matter. In set-associative cache, there may be a problem when we are only working with data cells that all map to the same cache line. When is this the case? When we are considering memory locations that are all have the same remainder modulo some large power of two.

Unfortunately, this happens quite often, as we programmers love using powers of two for our algorithms and data structures.

Fortunately, this is easy to fix: just don't use powers of two. Not necessarily for the algorithm, but at least for the memory layout.

### Acknowledgements

This article is inspired by http://igoro.com/archive/gallery-of-processor-cache-effects/ by Igor Ostrovsky.

For a more a comprehensive read, consider "[What Every Programmer Should Know About Memory](https://people.freebsd.org/~lstewart/articles/cpumemory.pdf)" by Ulrich Drepper.
