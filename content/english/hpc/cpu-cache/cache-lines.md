---
title: Cache Lines
weight: 3
---

- The CPU cache system operates on *cache lines*, which is the basic unit of data transfer between the CPU and the RAM. The size of a cache line is 64 bytes on most architectures, meaning that all main memory is divided into blocks of 64 bytes, and whenever you request (read or write) a single byte, you are also fetching all its 63 cache line neighbors whether your want them or not.


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

![](../img/permutation-padded.svg)
