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
