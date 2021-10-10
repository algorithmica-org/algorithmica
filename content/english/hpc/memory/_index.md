---
title: Memory
weight: 4
draft: true
---

In the beginning of the [previous chapter](../analyzing-performance), I used $5 \cdot 10^8$ as a rule of thumb for how many operations can be done in a second on average. Before going into how to go above that limit, first we need to learn how not to drop below it, and #1 reason for failing is memory.

Processors can't perform instructions directly on memory-stored data. Before doing anything, CPU always needs to load the data into internal storage locations called *registers*.

How long does it take to add two numbers together? The only correct answer to this question is: it depends. Mainly on where the operands are stored.

Being one of the most widely used instructions, `add` takes only one cycle to execute. So if the data is already in registers, it takes one cycle.

If the data is in the main memory (RAM), it will take around ~20ns, or about 30-40 CPU cycles, to fetch it, and another 30-40 cycles to write it back.

And on the extreme end, the data may be stored in hard drive, which takes around 5ms, which is $10^7$ cycles.

Because of such a high variance in performance, it is very important to optimize IO operations before doing anything else. Making sure you can feed data to your CPU should almost always be the highest priority.

## Memory Hierarchy

Modern computer memory is hierarchical. It consists of multiple *cache layers* of varying speed and size, where *upper* levels typically store most frequently accessed data from *lower* levels to reduce latency. Each new level is usually an order of magnitude faster, but also smaller and/or more expensive.

![](img/hierarchy.png)

Most programmers don't even need to think about this, as both hardware and software tries to abstract it away as much as possible. This is possible by the virtue of automatic caching of data based on the access times. This happens completely behind the scenes, and on lower levels programmers have very little control over it.

But for our needs, we need to study it deeper.

## Types of Memory

Memory devices can be abstractly described modules that have a certain storage capacity, and can read of write data in blocks of $B$ (not individual bytes), which is expected to take a specific time.

Abstractly, each type of memory has a few characteristics:
- Total size ($M$).
- Block size ($B$). 
- Latency. How much time it takes to get one byte.
- Bandwidth. It is not just block size times latency, but higher than that, meaning that you can "overlap" requests.
- Cost. This includes both cost of microchip, power, and maintenance. Pricing is ammortized. Total cost of ownership is complex, to calculate, as it includes the price for chip, energy requirements, maintenance, and capital appreciation.

Here is a comparison table that is approximately accurate for commodity hardware in 2021:

| Type | $M$      | $B$ | Latency | Bandwidth | $/GB/mo[^pricing] |
|:---- |:-------- | --- | ------- | --------- |:-------- |
| L1   | 10K      | 64B | 0.5ns   |           | -        |
| L2   | 100K     | 64B | 5ns     |           | -        |
| L3   | 1M/core  | 64B | 20ns    |           | -        |
| RAM  | GBs      | 64B | 100ns   |           | 1.5      |
| SSD  | TBs      | 4K  | 0.1ms   |           | 0.17     |
| HDD  | TBs      | -   | 10ms**  |           | 0.04     |
| S3   | $\infty$ | -   | 150ms   |           | 0.02[^S3]  |

Of course, there are specifics about each type, which we will go through.

[^S3]: There are multiple tiers, depending on how often you need that data.
[^pricing]: It is taken from GCP.

### Volatile Memory

The main distinction is between what happens in RAM and hard disks. The first is volatile. This means that it needs to be constantly powered, and will not persist data in case fo a shortage. Hence it is only used for essentially temporary data.

- **CPU registers.** These are the data cells. Access time is zero. There is only a very limited nubmer of them (e. g. 16 "general purpose" ones). In some cases you may want to use all your available registers.
- **CPU caches.** Modern ones have multiple layers. As of now, most commodity CPUs have 3 layers of cache and high-end ones have 4. L1 cache may take 3-4 cycles. Lower layers are shared between cores and are usually scale with the number of them (e. g. 10-core CPU will have around 10M or L3 cache). They come with CPUs themselves.
- **Random access memory.** You can increase. It takes about 100 cycles to read from RAM. One thing to note is that RAM and CPU caches have a concept.

Cache line is the unit of data transfer between CPU and main memory. The cache line of your PC is most likely 64 bytes, meaning that the main memory is divided into blocks of 64 bytes, and whenever you request a byte, you are also fetching its cache line neighbours regardless whether your want it or not.

### Non-Volatile Memory

- **Solid state drives.** These have latency of 0.1ms ($10^5$ ns)
- **Hard disk drive.** These are complicated, because HDD is actually a rotating physical thing with weird access patterns. [Video](https://www.youtube.com/watch?v=3owqvmMf6No&feature=emb_title)
- **Network-attached storage.** Simplest ones are NFS.

### Pagination

You can easily map non-volatile memory to behave like the normal one. In fact, this is the way it is mostly used, because it provides a convenient interface to file system.

RAM caching is transparent, but you need to use bufferization when working with external memory (e. g. HDD) unless it is [memmap](https://en.wikipedia.org/wiki/Mmap)-ed

It is much nicer to perform operations like if they were in memory.

Last thing to note is that main memory also has pagination.

![From John Bell\'s OS course at University of Illinois](img/virtual-memory.jpg)

---

We haven't covered some nuances, like how to [decide](eviction-policies) which blocks to keep in memory and which to discard, or the fact that you can perform requests [simultaneously](bandwidth-latency), but it will do for now.

