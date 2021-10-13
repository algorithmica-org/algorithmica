---
title: Memory
weight: 4
---

If a CPU core has a frequency of 3 GHz, it roughly means that it is capable of executing up to $3 \cdot 10^9$ operations per second, depending on what constitutes an "operation". This is the baseline: on modern architectures, it can be increased by techniques such as SIMD and instruction-level parallelism up to $10^{11}$ operations per second, if the computation allows it.

But for many algorithms, the CPU is not the bottleneck. Before trying to optimize performance above that baseline, we need to learn not to drop below it, and the number one reason for this is memory.

## A + B

To illustrate this point, consider this: how long does it take to add two numbers together? The only correct answer to this question is "it depends" — mainly on where the operands are stored.

Being one of the most frequently used instructions, `add` by itself only takes one cycle to execute. So if the data is already in registers, it takes one cycle. In general case (`*c = *a + *b`), it needs to fetch its operands from memory first:

```nasm
mov eax, DWORD PTR [rsi]
add eax, DWORD PTR [rdi]
mov DWORD PTR [rdx], eax
```

Typically, the data is stored in the main memory (RAM), and it will take around ~40ns, or about 100 cycles, to fetch it, and then another 100 cycles to write it back. If it was accessed recently, it is probably *cached* and will take less than that to fetch, depending on how long ago it was accessed — it could be ~20ns for the slowest layer of cache and under 1ns for the fastest. But it could also be that the data is stored on the hard drive, and in this case it will take around 5ms, or roughly $10^7$ cycles (!), to access it.

Because of such a high variance in performance, it is crucial to optimize IO operations before anything else.

## Memory Hierarchy

Modern computer memory is hierarchical. It consists of multiple *cache layers* of varying speed and size, where *upper* levels typically store most frequently accessed data from *lower* levels to reduce latency. Each new level is usually an order of magnitude faster, but also smaller and/or more expensive.

![](img/hierarchy.png)

Abstractly, various memory devices can be described as modules that have a certain storage capacity $M$ and can read or write data in blocks of $B$ (not individual bytes!), taking a fixed time to complete.

From this perspective, each type of memory has a few important characteristics:

- *total size* $M$;
- *block size* $B$; 
- *latency*, that is, how much time it takes to fetch one byte;
- *bandwidth*, which may be higher than just the block size times latency, meaning that IO operations can "overlap";
- *cost* in the amortized sense, including the price for chip, its energy requirements, maintenance and so on.

Here is an approximate comparison table for commodity hardware in 2021:

| Type | $M$      | $B$ | Latency | Bandwidth | $/GB/mo[^pricing] |
|:---- |:-------- | --- | ------- | --------- |:-------- |
| L1   | 10K      | 64B | 0.5ns   | 80G/s     | -        |
| L2   | 100K     | 64B | 5ns     | 40G/s     | -        |
| L3   | 1M/core  | 64B | 20ns    | 20G/s     | -        |
| RAM  | GBs      | 64B | 100ns   | 10G/s      | 1.5      |
| SSD  | TBs      | 4K  | 0.1ms   | 5G/s     | 0.17     |
| HDD  | TBs      | -   | 10ms    | 1G/s      | 0.04     |
| S3   | $\infty$ | -   | 150ms   | $\infty$  | 0.02[^S3]  |

Of course, in reality there are many specifics about each type of memory, which we will now go through.

[^pricing]: Pricing information is taken from Google Cloud Platform.
[^S3]: Cloud storage typically has multiple tiers, becoming progressively cheaper if you access the data less frequently.

### Volatile Memory

Everything up to the RAM level is called *volatile memory*, because it does not persist data in case of a power shortage and other disasters. It is fast, which is why it is used to store temporary data while the computer is powered.

From fastest to slowest:

- **CPU registers**, which are the zero-time access data cells CPU uses to store all its intermediate values, can also be thought of as a memory type. There is only a very limited number of them (e. g. 16 "general purpose" ones), and in some cases you may want to use all of them for performance reasons.
- **CPU caches.** Modern CPUs have multiple layers of cache (L1, L2, often L3, and rarely even L4). The lowest layer is shared between cores and is usually scaled with the their number (e. g. a 10-core CPU should have around 10M of L3 cache).
- **Random access memory,** which is the first scalable type of memory: nowadays you can rent machines with half a terabyte of RAM on the public clouds. This is the one where most of your working data is supposed to be stored.

The CPU cache system has an important concept of a *cache line*, which is the basic unit of data transfer between the CPU and the RAM. The size of a cache line is 64 bytes on most architectures, meaning that all main memory is divided into blocks of 64 bytes, and whenever you request (read or write) a single byte, you are also fetching all its 63 cache line neighbors whether your want them or not.

Caching on the CPU level happens automatically based on the last access times of cache lines. When accessed, the contents of a cache line are emplaced onto the lowest cache layer, and then gradually evicted to a lower levels unless accessed again in time. The programmer can't control this process explicitly, but it is worthwhile to study how it works in detail, which we will do later in this chapter.

Caching is done not with a separate chip, but is embedded in the CPU itself. There are also multi-socket systems that support installing multiple CPUs in the motherboard. In this case, they have separate caching systems, and more over, each socket often becomes *local* to a certain part of the main memory and thus has increased latency (~100ns) for accessing locations outside of it. Such architectures are called NUMA ("Non-Uniform Memory Access") and used as a way to increase the total amount of RAM. We will not consider them for now, but they will become important in the context of parallel computing.

There are other caches inside CPUs that are used for something other than data. Instructions are fetched from memory roughly the same way that the data is fetched, so it is important not to wait for the instructions to load. For this reason, CPUs also have *instruction cache*, which, as the name suggests, is used for caching instructions that are read from the main memory. Its size and performance are about the same as for the L1 cache, and since it is not large, it makes sense to make binaries small in size so that the CPU does not "starve" from not being to fetch instructions in time.

### Non-Volatile Memory

While the data cells in CPU caches and the RAM only gently store just a few electrons (that periodically leak and need to be periodically refreshed), the data cells in *non-volatile memory* types store hundreds of them. This lets the data to be persisted for prolonged periods of time without power, but comes at the cost of performance and durability — because when you have more electrons, you also have more opportunities for them colliding with silicon atoms.

<!-- error correction -->

There are many ways to store data in a persistent way, but these are the main ones from a programmer's perspective:

- **Solid state drives.** These have relatively low latency on the order of 0.1ms ($10^5$ ns), but they also have high cost, amplified by the fact that they have limited lifespans as each cell can only be written to a limited number of times. This is what mobile devices and most laptops use, because they are compact and have no moving parts.
- **Hard disk drives** are unusual because they are actually [rotating physical disks](https://www.youtube.com/watch?v=3owqvmMf6No&feature=emb_title) with a read/write head attached to them. To read a memory location, you need to wait until the disk rotates to the right position and then very precisely move the head to it. This results in some very weird access patterns where reading one byte randomly may take the same time as reading the next 1MB of data — which is usually on the order of milliseconds. Since this is the only part of a computer, except for the cooling system, that has mechanically moving parts, hard disks break quite often (with the average lifespan of ~3 years for a data center HDD).
- **Network-attached storage**, which is the practice of using other networked devices to store data on them. There are two distinctive types. The first one is the Network File System (NFS), which is a protocol for mounting other computer's file system over the network. The other is API-based distributed storage systems, most famously [Amazon S3](https://aws.amazon.com/s3/), that are backed by a fleet of storage-optimized machines of a public cloud, typically using cheap HDDs or some [more exotic](https://aws.amazon.com/storagegateway/vtl/) storage types internally. While NFS can can sometimes work even faster than HDD if located in the same data center, object storage in the public cloud usually has latencies of 50-100ms. They are typically highly distributed and replicated for better availability.

Since SDD/HDD are noticeably slower than RAM, everything on or below this level is usually called *external memory*.

Unlike the CPU caches, external memory can be explicitly controlled. This is useful in many cases, but most programmers just want to abstract away from it and use it as an extension of the main memory, and operating systems have the capability to do so by the virtue of *memory paging*.

Modern operating systems give every process the impression that it is working with large, contiguous sections of memory, called *virtual memory*. Physically, the memory allocated to each process may be dispersed across different areas of physical memory, or may have been moved to another storage such as SSD or HDD.

Do achieve this, the address space of the virtual memory is divided into *pages* (typically 4KB in size), and the memory system maintains a separate hardware data structure called *page table*, which points to where the data is physically stored for each page. When a process requests access to data in its memory, the operating system maps the virtual address to the physical address through the page table and forwards the read/write request to where that data is actually stored.

Since the address translation needs to be done for each memory request, this process is also cached with what's called *translation lookaside buffer* (TLB), which is just a very small cache for physical page addresses. When it doesn't hit, you essentially pay double the cost of a memory access. For this reason, some operating systems have support for larger pages (~2MB).

![From John Bell\'s OS course at University of Illinois](img/virtual-memory.jpg)

This mechanism allows using external memory quite transparently. Operating systems have two basic mechanisms:

- *Swap files*, which let the operating system automatically use parts of an SDD or an HDD as an extension of RAM when there is not enough real RAM.
- [Memory mapping](https://en.wikipedia.org/wiki/Mmap), which lets you open a file a use its contents as if they were in the main memory.

This essentially turns your RAM into "L4 cache" for the external memory, which is a good way to reason about it.
