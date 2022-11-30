---
title: Theoretical Performance Limits
weight: 5
draft: true
---

Do I want to talk about it here or in ILP section?

- Decode width
- Throughput of a certain instruction or, more precisely, an execution port
- Instruction Latency (on critical path)
- 
- Cache/Memory latency
- Cache/Memory throughput


A very good model is identifying the bottleneck and then working around it.

### Decode Width

Add two arrays together and write into a third.

Thanks to fused operations.

### Memory-Bandwidth Algorithm

Single-pass SIMD algorithms are going to be bottlenecked by memory.

### Memory-Latency

You need $n$ random memory accesses. Each .

However hard you try, you can't make the latency lower than the slowest memory read.

### Comparison-Based Sorting

### Linear Algebra

There is an FMA instruction.

This is the number usually reported.

**Exercise: theoretical peak performance.** By the way, assuming infinite bandwidth, what would the throughput of that loop be? How to verify that the 14 GFLOPS figure is the CPU limit and not L1 peak bandwidth? For that we need to look a bit closer at how the processor will execute the loop.

Incrementing an array can be done with SIMD; when compiled, it uses just two operations per 8 elements — performing the read-fused addition and writing the result back:

```asm
vpaddd  ymm0, ymm1, YMMWORD PTR [rax]
vmovdqa YMMWORD PTR [rax], ymm0
```

This computation is bottlenecked by the write, which has a throughput of 1. This means that we can theoretically increment and write back 8 values per cycle on average, yielding the performance of 2 GHz × 8 = 16 GFLOPS (or 32.8 in boost mode), which is fairly close to what we observed.

On all modern architectures, you can typically assume that you won't ever be bottlenecked by the throughput of L1 cache, but rather by the read/write execution ports or the arithmetic. In these extreme cases, it may be beneficial to store some data in registers without touching any of the memory, which we will cover later in the book.
