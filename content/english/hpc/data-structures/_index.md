---
title: Data Structures Case Studies
weight: 12
---

Optimizing data structures is different from optimizing [algorithms](/hpc/algorithms) as data structure problems have more dimensions: you may be optimizing for *throughput*, for *latency*, for *memory usage*, or any combination of those — and this complexity blows up exponentially when you need to process *multiple* query types and consider multiple query distributions.

This makes simply [defining benchmarks](/hpc/profiling/noise/) much harder, let alone the actual implementations. In this chapter, we will try to navigate all this complexity and learn how to design efficient data structures with extensive case studies.

A brief review of the [CPU cache system](/hpc/cpu-cache) is strongly advised.
