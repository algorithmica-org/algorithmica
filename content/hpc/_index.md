---
title: High Performance Computing
menuTitle: HPC
weight: 5
authors:
- Sergey Slotin
created: "Feb 2021"
date: 2021-05-06
---

This is a work-in-progress Computer Science book titled "Algorithms for Modern Hardware".

Unlike a traditional book, this one will change over time, evolving in parallel with new improvements in hardware as well as software and my understanding of them.

All materials are hosted on GitHub, with code in a [separate repository](https://github.com/sslotin/scmm-code). This isn't a collaborative project, but any contributions and feedback are welcome.

### Disclaimer: Technology Choices

The examples in this book use C++, GCC, x86-64, CUDA and Spark, although the underlying principles we aim to convey are not specific to them.

To clear my conscience, I'm not happy with any of these choices: these technologies just happen to be the most widespread and stable at the moment, and thus more helpful for the reader. I would have respectively picked C / Rust, LLVM, arm, OpenCL and Dask; maybe there will be a 2nd edition in which some of the tech stack is changed.

## Table of Contents

## Part 1: Performance engineering

```
0. Why Big O Is Not so Relevant Anymore
1. Analyzing Performance
 1.1. Computer Architecture & Assembly
 1.2. Negotiating with Compilers
 1.3. Profiling
 1.4. Binary GCD                        <- 2x faster std::gcd
2. Bit Hacks and Arithmetic
 2.1. Floating-Point Arithmetic
 2.2. Integer and Modular Arithmetic
 2.3. Bit Manipulation
 2.4. Cryptography, Hashing and PRNG
 2.5. Integer Factorization
(2.6. Big Integers and FFT)
3. SIMD Parallelism
 3.1. Intrinsics and Vector Extensions
 3.2. Moving Data
 3.3. String Searching                  <- ?x faster strstr
 3.4. Parsing                           <- 2x faster scanf("%d")
(3.5. Sorting)                          <- 8x faster std::sort
(3.6. AVX-512 and Arm Neon)
4. Memory
 4.1. Memory Hierarchy
 4.2. External Memory Model
(4.3. Sublinear Algorithms)
 4.4. RAM & CPU Caches
(4.5. Memory Management)
 4.6. Layouts for Binary Search         <- 5x faster std::lower_bound
 4.7. Implicit Data Structures          <- 7x faster segment trees
 4.8. Hash Tables                       <- 5x faster std::unordered_map
5. Instruction-Level Parallelism
 5.1. Pipelining and Hazards
 5.2. Throughput Computing              <- 2x faster std::accumulate
(5.3. µOps & Scheduling)
 5.4. Theoretical Performance Limits
 5.5. Matrix Multiplication             <- 100x faster gemm
6. Summary
```

Release date: june 2021

### Part 2: Parallel Algorithms

Concurrency, models of parallelism, green threads and runtimes, cache coherence, syncronization primitives, OpenMP, reductions, scans, list ranking and graph algorithms, lock-free data structures, heterogenious computing, CUDA, kernels, warps, blocks, matrix multiplication and sorting.

Release date: fall 2021

### Part 3: Distributed Computing

Communication-constrained algorithms, message passing, actor model, partitioning, MapReduce, consistency and reliability at scale, storage, compression, scheduling and cloud computing, distributed deep learning.

Release date: 2022

### Part 4: Compilers and Domain Specific Architectures

LLVM IR, core optimization techniques from the dragon book, JIT-compilation, cython, jax, numba, julia, OpenCL, DPC++ and oneAPI, XLA, FPGAs and Verilog, ASICs, TPUs and other AI accelerators.

Release date: ???
