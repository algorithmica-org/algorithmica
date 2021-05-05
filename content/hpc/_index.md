---
title: High Performance Computing
menuTitle: HPC
weight: 5
authors:
- Sergey Slotin
created: "Feb 2021"
date: 2021-04-18
---

This is a work-in-progress Computer Science book titled "Supercomputing for Mere Mortals".

It is split in 3 parts:

1. [Performance Engineering](cpu), which is getting close to completion.
2. [Parallel Computing](parallel), which is still in the research stage.
3. [Distributed Computing](distributed), which doesn't even have a general curriculum yet.

Unlike a traditional book, this one will change over time, evolving in parallel with new improvements in hardware and software and my understanding of them.

All materials are hosted on GitHub, with code in a separate repository. This isn't a collaborative project, but any contributions and feedback are welcome.

### Disclaimer: Technology Choices

The examples in this book use C++, GCC, x86-64, CUDA and Spark, although the underlying principles we aim to convey are not specific to them.

To clear my conscience, I'm not happy with any of these choices: these technologies just happen to be the most widespread and stable at the moment, and thus more helpful for the reader. I would have respectively picked C / Rust, LLVM, arm, OpenCL and Dask; maybe there will be a 2nd edition in which some of the tech stack is changed.

### Table of Contents

Chapter 1:

```
0. Modern Hardware
1. Analyzing Performance
1.1. Computer Archicecture & Assembly
1.2. Compiler Optimizations
1.3. Profiling
1.4. Binary GCD                        <- 2x faster std::gcd
2. Memory
2.1. Memory Hierarchy
2.2. External Memory Model
2.3. RAM & CPU Caches
2.4. Memory Management
2.5. Layouts for Binary Search         <- 5x faster std::lower_bound
2.6. Implicit Data Structures          <- 7x faster segment trees
2.7. Hash Tables                       <- 5x faster std::unordered_map
3. Bit Hacks and Arithmetic
3.1. Floating-Point Arithmetic
3.2. Integer and Modular Arithmetic
3.3. Bit Manipulation
3.4. Hashing
3.5. Random Number Generation
3.6. Integer Factorization
4. SIMD Parallelism
4.1. Intrinsics
4.2. Vector Extensions
4.3. Moving Data
4.4. Lookup Tables and Popcount        <- 2x faster popcnt
4.5. Parsing                           <- 2x faster scanf("%d")
4.6. Sorting                           <- 8x faster std::sort
5. Instruction-Level Parallelism
5.1. Pipelining
5.2. Hazards
5.3. Throughput Computing              <- 2x faster std::accumulate
5.4. µOps & Scheduling
5.5. Theoretical Limits
5.6. Matrix Multiplication             <- 100x faster gemm
6. Summary
```
