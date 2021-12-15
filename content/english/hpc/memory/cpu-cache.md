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

- 8 physical cores (without hyper-threading) clocked at 2GHz[^boost];
- 512K of 8-way set associative L1 cache, half of which is instruction cache — meaning 32K per core;
- 4M of 8-way set associative L2 cache, or 512K per core;
- 8M of 16-way set associative L3 cache, *shared* between 8 cores (4M actually);
- 16G of DDR4 RAM @ 2667MHz.

[^boost]: Although the CPU can be clocked at 4.1GHz in boost mode, we will perform most experiments at 2GHz to reduce noise — so keep in mind that in realistic applications the numbers can be multiplied by 2.

You can compare it with your own hardware by running `dmidecode -t cache` or `lshw -class memory` on Linux or just looking it up on WikiChip.

Due to difficulties in [refraining compiler from cheating](..//hpc/analyzing-performance/profiling/), the code snippets in this article are be slightly simplified for exposition purposes. Check the [code repository](https://github.com/sslotin/amh-code/tree/main/cpu-cache) if you want to reproduce them yourself.

I am not going to turn off frequency boosting or silence other programs while doing these benchmarks. The goal is to get realistic values, like when optimizing a video game.

## Memory Bandwidth

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

### Cache Sharing

Starting from a certain level in the hierarchy, cache becomes shared between different cores. This limits the size and bandwidth of the cache, reducing performance in case of parallel algorithms or just noisy neighbors.

On my machine, there is actually not 4M, but 8M of L3 cache, but it is shared between groups of 4 cores so that each core "sees" only 4M that is shared with 3 other cores — and, of course, all the cores have uniform access to RAM. There may be more complex situations, especially in the case of multi-socket and NUMA architectures. The "topology" of the cache system can be retrieved with the `lstopo` utility.

![Cache hierarchy scheme generated by lstopo command on Linux](../img/lstopo.png)

This has some very important implications for certain parallel algorithms:

- If and algorithm is memory-bound, then it doesn't matter how much cores you add, as it will be bottlenecked by the RAM bandwidth.
- On non-uniform architectures, it matters which cores are running which execution threads.

To show this, we can run the same benchmarks in parallel. Instead of changing source code to run multiple threads, we can make use of GNU parallel. Due to the asymmetry `taskset` to manage CPU affinity and set them to the first "half" of cores (to temporary ignore the second issue).

```bash
parallel taskset -c 0,1,2,3 ./run ::: {0..3}
```

You can now see that the L3 effects diminishes with more cores competing for it, and after falling into the RAM region the total performance remains constant.

![](../img/parallel.svg)

This asymmetry makes it important to manage where exactly different threads should be running. By default, the operating systems knows nothing about affinity, so it assigns threads to cores arbitrarily and dynamically during execution, based on core load and job priority, and settings of the scheduler. This can be affected directly, which is what we did with taskset to restrict the available cores to the first half that share the same 4M region of L3.

Let's add another 2-thread run, but now with running on cores in different 4-core groups that don't share L3 cache:

```bash
parallel taskset -c 0,1 ./run ::: {0..1}
parallel taskset -c 0,4 ./run ::: {0..1}
```

You can see that it performs better — as if there were twice as much L3 cache available.

![](../img/affinity.svg)

These issues are especially tricky when benchmarking and is usually the largest source of noise in real-world applications.

### Cache Lines

The most important feature of the memory system is that it deals with cache lines, and not individual bytes.

To demonstrate this, let's add "step" parameter to our loop — we will now increment every $D$-th element:
 
```cpp
for (int t = 0; t < K; t++)
    for (int i = 0; i < N; i += D)
        a[i]++;
```

When we run it with $D=16$, we can observe something interesting:

![Performance is normalized by the total time to run benchmark, not the total number of elements incremented](../img/strided.svg)

As the problem size grows, the graphs of the two loops meet, despite one doing 16 times less work than the other. This is because in terms of cache lines, we are fetching exactly the same memory; the fact that the strided computation only needs one sixteenth of it is irrelevant.

It does work a bit faster when the array fits into lower layers of cache because the loop becomes much simples: all it does is `inc DWORD PTR [rdx]` (yes, x86 has instructions that only involve memory locations and no registers or immediate values). It also has a throughput of one, but while the former code needed to perform two of writes per cache line, this only needs one, hence it works twice as fast when memory is not a concern.

When we change the step parameter to 8, the graphs equalize:

![](../img/strided2.svg)

The important lesson is to count the number of cache lines to fetch when analyzing memory-bound algorithms, and not the total count of memory accesses. This becomes increasingly important with larger problem sizes.

### Memory Paging

Let's consider other possible values of $D$ and try to measure loop performance. Since for values larger than 16 we will skip some cache lines altogether, requiring less memory reads and fewer cache, we change the size of the array so that the total number of cache lines fetched is constant.

```cpp
const int N = (1 << 13);
int a[D * N];

for (int i = 0; i < D * N; i += D)
    a[i] += 1;
```

All we change now is the stride, and $N$ remains constant. It is equal to $2^{13}$ cache lines or $2^{13} \cdot 2^6 = 2^{19}$ bytes, precisely so that the entire addressable array can fit into L2 cache, regardless of step size. The graph should look flat, but this is not what happens.

![](../img/strides.svg)

This anomaly is due to the cache system, but the standard L1-L3 data caches have nothing to do with it. *Memory paging* is at fault, in particular the type of cache called *translation lookaside buffer* (TLB) that is responsible for retrieving the physical addresses of 4K memory pages of virtual memory.

On our CPU, there is not one, but two layers of TLB cache. L1 TLB can house 64 entries for a total $64 \times 4K = 512K$ of data, and L2 TLB has 2048 entries for a total of $2048 \times 4K = 8M$, which is — surprise-surprise — exactly the array size at the point where the cliff starts ($8K \times 256 \times 4B = 8M$). You can fetch this information for your architecture with `cpuid` command.

This is a huge issue, as such access patterns when we need to jump large distances are actually quite common in real programs too. Why not just make page size larger? This reduces granularity of system memory allocation — increasing fragmentation. So modern operating systems actually give us freedom in choosing page size on demand. You can read more on madvise if you are interested, but for our benchmarks we will just turn on huge pages for all allocations by default like this:

```bash
echo always >/sys/kernel/mm/transparent_hugepage/enabled
```

This flattens the curve:

![](../img/strides-hugepages.svg)

Typical size of a page is 4KB, but it can be up to 1G or so for large databases, but enabling it by default is not a good idea as scenarios when we have a VPS with 256M or RAM and more than 256 processes are not uncommon.

Typical page sizes are 4K, 2M and 1G (e. g. allowing for 256K, 128M, 64G memory regions to be stored in a 64-entry L1 TLB respectively).

### Cache Associativity

If you looked carefully, you could notice patterns while inspecting the dots below the graph in the previous experiment. These are not just noise: certain step sizes indeed perform much worse than their neighbors.

For example, the stride of 256 corresponding to this loop:

```cpp
for (int i = 0; i < N; i += 256)
    a[i]++;
```

and this one

```cpp
for (int i = 0; i < N; i += 257)
    a[i]++;
```

differ by more than 10x: 256 runs at 0.067 while 257 runs at 0.751.

This is not just a single specific bad value: it is the same for all indices that are multiple of large powers of two, and it continues much further to the right.

![](../img/strides-two.svg)

This effect is due to a feature called *cache associativity*, and an interesting artifact of how CPU caches are implemented in hardware.

When studying memory theoretically using the external memory model, we discussed different ways one can [implement caching policies](/hpc/memory/locality/) in software, and went into detail on particular case of a simple but effective strategy, LRU, which required some non-trivial data manipulation. In the context of hardware, such scheme is called *fully associative cache*.

![Fully associative cache](../img/cache2.png)

The problem with it is that implementing something like that is prohibitively expensive. In hardware, you can implement something when you have 16 entries or so, but it becomes unfeasible when it comes to storing and managing hundreds of cache lines.

We can resort to another, much simpler approach: we could just map each block of 64 bytes in RAM to a cache line which it can possibly occupy. Say if in we have 4096 blocks in memory and 64 cache lines for them, this means that each cache line at any time stores the value of one of $\frac{4096}{64} = 64$ different blocks, along with a "tag" information which helps identifying which block it is.

Simply speaking, the CPU just maintains these cells containing data, and when reading any cell from the main memory the CPU first looks it up in the cache, and if it contains the data, it reads it, and otherwise goes to a higher cache level until it reaches main memory. Simple and beautiful.

![Direct-mapped cache](../img/cache1.png)

Direct-mapped cache is easy to implement, but the problem with it is that the entries can be kicked out way too quickly, leading to lower cache utilization. In fact, we could just bounce between two addresses, leaving

For that reason, we settle for something in-between direct-mapped and fully associative cache: the *set-associative cache*. It splits addresses into groups which separately act as small fully-associative cache.

![Set-associative cache](../img/cache3.png)

*Associativity* is the size of such sets — for example 16 meaning that this way we would need to wait at least 16 reads for an entry to get kicked out. Different cache layers may have different associativity. Most CPU caches are set-associative, unless we are talking about small specialized ones that only house 64 or less entries and can get by with fully-associative schemes.

If we implemented cache in software, we would compute some hash function to use as key. In hardware, we can't really do that because e. g. for L1 cache 4 or 5 cycles is all we got, and even taking a modulo takes 10-15 cycles, let alone something cryptographically secure. Therefore, hardware takes a different approach and calculates this address based on the address. It takes the address, and reinterprets it in three parts:

![](../img/address.png)

The last part is used for determining the cache line it is mapped to. All addresses with the same "middle" part will therefore map to the same set.

Now, where were we? Oh yes, the reason why iterating with strides of 256 has such a terrible slowdown. This because they all map to the same set, and effectively the size of the cache (and all below it) shrinks by 256/16=16. No longer being able to reside in L2, it spills all the way to the order-of-magnitude slower RAM, which causes the expected slowdown.

This issue arises with remarkable frequency in all types of algorithms that love powers of two. Luckily, this behavior is more of an anomaly than some that needs to be dealt with. The solution is usually simple: avoid iterating in powers of two, using different sizer on 2d arrays or inserting "holes" in the memory layout.

## Memory Latency

Despite bandwidth — how many data one can load — is a more complicated concept, it is much easier to observe and measure than latency — how much time it takes to load one cache line.

Measuring memory bandwidth is easy because the CPU can simply queue up multiple iterations of data-parallel loops like the one above. The scheduler gets access to the needed memory locations far in advance and can dispatch read requests in a way that will overlap all memory operations, hiding the latency.

To measure latency, we need to design an experiment where the CPU can't cheat by knowing the memory location in advance. We can do this like this: generate a random permutation of size $n$ that corresponds a full cycle, and then repeatedly follow the permutation.

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

This performance anti-pattern is known as *pointer chasing*, and it very frequent in software, especially written in high-level languages. Iterating an array this way is considerably slower.

![](../img/permutation-latency.svg)

When speaking of latency, it makes more sense to use cycles or nanoseconds rather than bandwidth units. So we will replace this graph with its reciprocal:

![](../img/latency-throughput.svg)

It is generally *much* slower — by multiple orders of magnitude — to iterate an array this way. Not only because it makes SIMD practically impossible, but also because it stalls the pipeline a lot.

### Latency of RAM and TLB

![](../img/permutation-boost.svg)

It becomes more clear when looking at the relative speedup:

![](../img/permutation-boost-speedup.svg)

By the way, how does TLB affect latency?

The TLB cache is called "lookaside" because the lookup can happen independently from normal data cache lookups.

So, the effect is independent.

It is "lookaside" is because it is looked up concurrently with the accesses in the cache. First layer typically uses virtual addresses anyway. Memory controller retrieves entries in cache and TLB, and then compares the tag.

Paging is implemented both on software (OS) and hardware level.

TLB cache which is used for storing.

It is possible, but quite tedious to also construct an experiment actually measuring all this — so you will have to take my word on that one.

### Pointers

The latency of L1 fetch is 4 or 5 cycles, the latter being the case if we need to use fused computation of address. In theory, it works slightly faster if we are working with actual pointers.

```cpp
// pointer implementation
```

IMAGE

On 64-bit architectures, the pointers are all 64-bit (despite only using 48 bits), so the array takes a bit more space and falls off cache more quickly. On 32-bit, it should be slightly faster.

IMAGE: original, 64-bit pointers, 32-bit pointers

Graph looks like if it was shifted by 1 to the left — exactly like it should.

When iterating over arrays, the latency is hidden by *prefetching* — implicit or explicit. You should design your algorithms in a way that allows for this sort of concurrency.

### Pointers

There are some syntactical issues in getting "pointer to pointer to pointer…" constructions to work, so instead we will define a struct type that just wraps a pointers to its own kind — this is how most pointer chasing works anyway:

```cpp
struct node { node* ptr; };
```

Now we fill our array with pointers:

```cpp
node

for (int i = 0; i < N; i++) {
    q[k].ptr = q + p[i];
    k = p[i];
}


for (int i = 0; i < N; i++)
    ptr = ptr->ptr;
```

After going [through some trouble](https://askubuntu.com/questions/91909/trouble-compiling-a-32-bit-binary-on-a-64-bit-machine) getting 32-bit libs to get this running on a computer made in this century.

Tip: use raw pointers when you can.

### Pipelining and Speculative Execution

*Implicit prefetching*: memory reads can be speculative too, and reads will be pipelined anyway.

In fact, this sometimes works even when we are not sure which branch is going to be executed next — because, well, we wait for a hundred cycles anyway, why not evaluate at least one of the branches ahead of time?

```cpp
bool cond = some_long_memory_operation();

if (cond)
    do_this_fast_operation();
else
    do_that_fast_operation();
```

(By the way, this is what Meltdown was all about)

### Hardware Prefetching

Hiding latency is crucial — it is pretty much the single most important idea we keep coming back to in this book. Apart from having a very large pipeline and using the fact that scheduler can look ahead in it, modern memory controllers can detect simple patterns such as iterating backwards, forwards, including using constant small-ish strides.

Here is how to test it: we now generate our permutation in a way that makes us load consecutive cache lines, but we fetch elements in random order inside the cache lines.

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

The performance is almost on par with linear iteration:

IMAGE HERE

Hardware prefetching is usually powerful enough for most cases. You can iterate over multiple arrays, sometimes with small strides, or load just small amounts. It is as intelligent — and as detrimental to performance — as branch prediction.

### Software Prefetching

Sometimes the CPU can't figure it out by itself. In this case, we need to point it explicitly.

The easiest thing is to just use any byte in the cache line as an operand, but CPUs have an explicit instruction to just "lift" a cache line without doing anything with it. As far as I know, this instruction is not a part of the C/C++ standard or any other language, but is widely available in compilers.

It turned out it is non-trivial to design such a permutation case that simultaneously loops around all the array, can't be predicted by hardware prefetching but the next address is easily computable in order to do prefetching.

Luckily, LCG can be used. It is a known property that if ..., then the period will be exactly $n$. So, we will modify our algorithm so that the permutation is generated by LCG, using current index as the state:

```cpp
const int n = find_prime(N);

for (int i = 0; i < n; i++)
    q[i] = (2 * i + 1) % n;
```

Running it, the performance is the same as with the fully random permutation. But now we have the capability of peeking a bit ahead:

```cpp
int k = 0;

for (int t = 0; t < K; t++) {
    for (int i = 0; i < n; i++) {
        __builtin_prefetch(&q[(2 * k + 1) % n]);
        k = q[k];
    }
}
```

It is almost 2 times faster, as we expected. Interestingly, we can cut it arbitrarily close (to the cost of computing the next index — [modulo is expensive](../arithmetic/integer)).

One can show that in order to load $k$-th element ahead, we can do this:

```cpp
__builtin_prefetch(&q[((1 << D) * k + (1 << D) - 1) % n]);
```

Managing issues such as integer overflow, we can cut latency down.

<!--
Instruction Cache. Unrolling loops. Aligning. No-op.
-->

## Summary and Lessons Learned

Our experiments suggest the following:

| Type | $M$      | $B$ | Latency | Bandwidth | $/GB/mo[^pricing] |
|:-----|:---------|-----|---------|-----------|:------------------|
| L1   | 10K      | 64B | 0.5ns   | 80G/s     | -                 |
| L2   | 100K     | 64B | 5ns     | 40G/s     | -                 |
| L3   | 1M/core  | 64B | 20ns    | 20G/s     | -                 |
| RAM  | GBs      | 64B | 100ns   | 10G/s     | 1.5               |
| SSD  | TBs      | 4K  | 0.1ms   | 5G/s      | 0.17              |
| HDD  | TBs      | -   | 10ms    | 1G/s      | 0.04              |
| S3   | $\infty$ | -   | 150ms   | $\infty$  | 0.02[^S3]         |

(transform it to just text)

We can learn valuable lessons from our experiments. There are two types of memory-bound algorithms. Loops or data structures.

**Latency-constrained.** For the purpose of designing algorithms, a more important characteristic is the **bandwidth-latency product** which basically tells how many cache lines you can request while waiting for the first one without queueing up. It is around 5 or more on most systems. CPUs can detect simple patterns such as linear iteration forward or backward.

**Bandwidth-constrained.** We started the previous section with how it is not relevant which algorithm is used to determine cache eviction. In most practical cases, this is really the case.

But in some cases the specifics start to matter. In set-associative cache, there may be a problem when we are only working with data cells that all map to the same cache line. When is this the case? When we are considering memory locations that are all have the same remainder modulo some large power of two.

Unfortunately, this happens quite often, as we programmers love using powers of two for our algorithms and data structures.

Fortunately, this is easy to fix: just don't use powers of two. Not necessarily for the algorithm, but at least for the memory layout.

https://www.7-cpu.com/cpu/Zen2.html

## Further Reading

This article is inspired by "[Gallery of Processor Cache Effects](http://igoro.com/archive/gallery-of-processor-cache-effects/)" by Igor Ostrovsky.

For a more a comprehensive read, consider "[What Every Programmer Should Know About Memory](https://people.freebsd.org/~lstewart/articles/cpumemory.pdf)" by Ulrich Drepper.

More fundamental [academic paper](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1993/CSD-93-767.pdf) by Rafael Saavedra and Alan Smith.
