---
title: Memory Paging
weight: 7
---

- There are other types of cache inside CPUs that are used for things other than data. The most important for us are *instruction cache* (I-cache), which is used to speed up the fetching of machine code from memory, and *translation lookaside buffer* (TLB), which is used to store physical locations of virtual memory pages, which is instrumental to the efficiency of virtual memory.


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

This is a huge issue, as such access patterns when we need to jump large distances are actually quite common in real programs too. Why not just make page size larger? This reduces granularity of system memory allocation — increasing fragmentation. Paging is implemented both on software (OS) and hardware level, and modern operating systems actually give us freedom in choosing page size on demand. You can read more on madvise if you are interested, but for our benchmarks we will just turn on huge pages for all allocations by default like this:

```bash
echo always >/sys/kernel/mm/transparent_hugepage/enabled
```

This flattens the curve:

![](../img/strides-hugepages.svg)

Typical size of a page is 4KB, but it can be up to 1G or so for large databases, but enabling it by default is not a good idea as scenarios when we have a VPS with 256M or RAM and more than 256 processes are not uncommon.

Typical page sizes are 4K, 2M and 1G (e. g. allowing for 256K, 128M, 64G memory regions to be stored in a 64-entry L1 TLB respectively).

You can only request if it has alignment.

```c++
#include <sys/mman.h>

void *ptr = std::aligned_alloc(page_size, array_size);
madvise(pre, array_size, MADV_HUGEPAGE);
```

On Windows, this operation is fused:

```c++
#include "memoryapi.h"

void *ptr = VirtualAlloc(NULL, array_size,
                         MEM_RESERVE | MEM_COMMIT | MEM_LARGE_PAGES, PAGE_READWRITE);
```

In both cases, `array_size` should be a multiple of `page_size`.

![](../img/permutation-hugepages.svg)


### Other Blocks

Pages

RAM rows. 3-4 nanosecond increase.


<!--

Actually, TLB misses may stall memory reads for the same reason. The TLB cache is called "lookaside" because the lookup can happen independently from normal data cache lookups. L1 and L2 caches on the other side are private to the core, and so they can store virtual addresses and be queried concurrently with TLB — after fetching a cache line, its tag is used to restore the physical address, which is then checked against the concurrently fetched TLB entry. This trick does not work for shared memory however, because their bandwidth is limited, and dispatching read queries there for no reason is not a good idea in general. So we can observe a similar effect in L3 and RAM reads when the page does not fit L1 TLB and L2 TLB respectively.

For sparse reads, it often makes sense to increase page size, which improves the latency.

It is possible, but quite tedious to also construct an experiment actually measuring all this — so you will have to take my word on that one.

-->

