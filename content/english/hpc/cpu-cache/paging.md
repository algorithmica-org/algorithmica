---
title: Memory Paging
weight: 12
---

Consider [yet again](../associativity) the strided incrementing loop:

```cpp
const int N = (1 << 13);
int a[D * N];

for (int i = 0; i < D * N; i += D)
    a[i] += 1;
```

We change the stride $D$ and increase the array size proportionally so that the total number of iterations $N$ remains constant. As the total number of memory accesses also remains constant, for all $D \geq 16$, we should be fetching exactly $N$ cache lines — or $64 \cdot N = 2^6 \cdot 2^{13} = 2^{19}$ bytes, to be exact. This precisely fits into the L2 cache, regardless of the step size, and the throughput graph should look flat.

This time, we consider a larger range of $D$ values, up to 1024. Starting from around 256, the graph is definitely not flat:

![](../img/strides.svg)

This anomaly is also due to the cache system, although the standard L1-L3 data caches have nothing to do with it. [Virtual memory](/hpc/external-memory/virtual) is at fault, in particular the *translation lookaside buffer* (TLB), which is a cache responsible for retrieving the physical addresses of the virtual memory pages.

On [my CPU](https://en.wikichip.org/wiki/amd/microarchitectures/zen_2), there are two levels of TLB:

- The L1 TLB has 64 entries, and if the page size is 4K, then it can handle $64 \times 4K = 512K$ of active memory without going to the L2 TLB.
- The L2 TLB has 2048 entries, and it can handle $2048 \times 4K = 8M$ of memory without going to the page table.

How much memory is allocated when $D$ becomes equal to 256? You've guessed it: $8K \times 256 \times 4B = 8M$, exactly the limit of what the L2 TLB can handle. When $D$ gets larger than that, some requests start getting redirected to the main page table, which has a large latency and very limited throughput, which bottlenecks the whole computation.

### Changing Page Size

That 8MB of slowdown-free memory seems like a very tight restriction. While we can't change the characteristics of the hardware to lift it, we *can* increase the page size, which would in turn reduce the pressure on the TLB capacity.

Modern operating systems allow us to set the page size both globally and for individual allocations. CPUs only support a defined set of page sizes — mine, for example, can use either 4K or 2M pages. Another typical page size is 1G — it is usually only relevant for server-grade hardware with hundreds of gigabytes of RAM. Anything over the default 4K is called *huge pages* on Linux and *large pages* on Windows.

On Linux, there is a special system file that governs the allocation of huge pages. Here is how to make the kernel give you huge pages on every allocation:

```bash
$ echo always > /sys/kernel/mm/transparent_hugepage/enabled
```

Enabling huge pages globally like this isn't always a good idea because it decreases memory granularity and raises the minimum memory that a process consumes — and some environments have more processes than free megabytes of memory. So, in addition to `always` and `never`, there is a third option in that file:

```bash
$ cat /sys/kernel/mm/transparent_hugepage/enabled
always [madvise] never
```

`madvise` is a special system call that lets the program advise the kernel on whether to use huge pages or not, which can be used for allocating huge pages on-demand. If it is enabled, you can use it in C++ like this:

```c++
#include <sys/mman.h>

void *ptr = std::aligned_alloc(page_size, array_size);
madvise(ptr, array_size, MADV_HUGEPAGE);
```

You can only request a memory region to be allocated using huge pages if it has the corresponding alignment.

Windows has similar functionality. Its memory API combines these two functions into one:

```c++
#include "memoryapi.h"

void *ptr = VirtualAlloc(NULL, array_size,
                         MEM_RESERVE | MEM_COMMIT | MEM_LARGE_PAGES, PAGE_READWRITE);
```

In both cases, `array_size` should be a multiple of `page_size`.

### Impact of Huge Pages

Both variants of allocating huge pages immediately flatten the curve:

![](../img/strides-hugepages.svg)

Enabling huge pages also improves [latency](../latency) by up to 10-15% for arrays that don't fit into the L2 cache:

![](../img/permutation-hugepages.svg)

In general, enabling huge pages is a good idea when you have any sort of sparse reads, as they usually slightly improve and ([almost](../aos-soa)) never hurt performance.

That said, you shouldn't rely on huge pages if possible, as they aren't always available due to either hardware or computing environment restrictions. There are [many](../cache-lines) [other](../prefetching) [reasons](../aos-soa) why grouping data accesses spatially may be beneficial, which automatically solves the paging problem.

<!--


virtually located, physically tagged

Actually, TLB misses may stall memory reads for the same reason. The TLB cache is called "lookaside" because the lookup can happen independently from normal data cache lookups. L1 and L2 caches on the other side are private to the core, and so they can store virtual addresses and be queried concurrently with TLB — after fetching a cache line, its tag is used to restore the physical address, which is then checked against the concurrently fetched TLB entry. This trick does not work for shared memory however, because their bandwidth is limited, and dispatching read queries there for no reason is not a good idea in general. So we can observe a similar effect in L3 and RAM reads when the page does not fit L1 TLB and L2 TLB respectively.

For sparse reads, it often makes sense to increase page size, which improves the latency.

Typical size of a page is 4KB, but it can be up to 1G or so for large databases, but enabling it by default is not a good idea as scenarios when we have a VPS with 256M or RAM and more than 256 processes are not uncommon.

Typical page sizes are 4K, 2M and 1G (e.g., allowing for 256K, 128M, 64G memory regions to be stored in a 64-entry L1 TLB respectively).


- There are other types of cache inside CPUs that are used for things other than data. The most important for us are *instruction cache* (I-cache), which is used to speed up the fetching of machine code from memory, and *translation lookaside buffer* (TLB), which is used to store physical locations of virtual memory pages, which is instrumental to the efficiency of virtual memory.

You can fetch this information for your architecture with `cpuid` command.

-->

