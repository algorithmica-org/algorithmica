---
title: RAM & CPU Caches
weight: 4
draft: true
---

In previous sections of this chapter, we mostly studied the theoretical side and did a lot of hand waving when it came to real implementations. In this section, we will study the RAM and CPU cache system in higher detail.

We will do so while doing actual measurements.

To recall, we are running Ryzen 4700U @ 4.1GHz. Its specs are as follows:

- 
- 
- 
- 

You can get these stats for your chip by calling `dmidecode -t cache` and `dmidecode -t cache` on Linux or looking it up on WikiChip.

Like in physics, we will try to measure it experimentally.

## Memory Latency

Permutation.

Pointer chasing

## Cache Lines

Burst memory.

## Memory Bandwidth

### Prefetching

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

For a more comprehensive reading, consider "[What Every Programmer Should Know About Memory](https://people.freebsd.org/~lstewart/articles/cpumemory.pdf)" by Ulrich Drepper.
