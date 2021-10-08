---
title: Algorithms for Modern Hardware
menuTitle: HPC
weight: 5
authors:
- Sergey Slotin
#created: "Feb 2021"
date: 2021-09-16
noToc: true
---

This is a work-in-progress High Performance Computing book titled "Algorithms for Modern Hardware".

It is intended for performance engineers as well as CS students who have just finished an advanced algorithms course and want to learn more practical ways to speed up a program than by going from $O(n \log n)$ to $O(n \log \log n)$.

All materials are hosted on GitHub, with code in a [separate repository](https://github.com/sslotin/scmm-code). This isn't a collaborative project, but any contributions and feedback are welcome.

### Part I: Performance Engineering

The first part covers the basics of computer architecture and optimization of single-threaded algorithms.

```
0. Why Go Beyond Big O
1. Analyzing Performance
 1.1. Computer Architecture & Assembly
 1.2. Negotiating with Compilers
 1.3. Profiling
 1.4. Binary GCD                        <- 2x faster std::gcd
2. Bit Hacks and Arithmetic
 2.1. Floating-Point Arithmetic
 2.2. Numerical Methods
 2.3. Integer Arithmetic
 2.4. Bit Manipulation
 2.5. Modular Arithmetic
 2.6. Finite Fields
 2.7. Cryptography, Hashing and PRNG
 2.8. Integer Factorization
 2.9. Bignum Arithmetic and the Karatsuba Algorithm
 2.10. Fast Fourier Transform
3. SIMD Parallelism
 3.1. Intrinsics and Vector Extensions
 3.2. (Auto-)Vectorization
 3.3. SSE & AVX Cookbook
 3.4. Argmin with SIMD
 3.5. Logistic Regression
 3.6. String Searching                  <- ?x faster strstr
 3.7. Parsing Integers                  <- 2x faster scanf("%d")
 3.8. Sorting                           <- 8x faster std::sort
4. Memory
 4.1. Memory Hierarchy
 4.2. External Memory Model
 4.3. Sublinear Algorithms
 4.4. RAM & CPU Caches
 4.5. Memory Management
 4.6. Layouts for Binary Search         <- 5x faster std::lower_bound
 4.7. Implicit Data Structures          <- 7x faster segment trees
 4.8. Hash Tables                       <- 5x faster std::unordered_map
5. Instruction-Level Parallelism
 5.1. Pipelining and Hazards
 5.2. Throughput Computing              <- 2x faster std::accumulate
 5.3. µOps & Scheduling
 5.4. Theoretical Performance Limits
 5.5. Matrix Multiplication             <- 100x faster gemm
6. Summary
```

It walks through the main CPU optimization techniques topics such as caching, SIMD and pipelining, and provides brief examples in C++ followed by large case studies where we usually achieve a significant speedup over some STL algorithm or data structure.

Among cool things that we will speed up, in chronological order:

- 2x faster GCD (compared to `std::gcd`)
- 4x faster binary search (compared to `std::lower_bound`)
- 7x faster segment trees
- 3x faster hash tables (compared to `std::unordered_map`)
- ?x faster popcount
- 1.7x faster parsing series of integers (compared to `scanf`)
- ?x faster sorting (compared to `std::sort`)
- 2x faster sum (compared to `std::accumulate`)
- 100x faster matrix multiplication (compared to "for-for-for")

This is largely based on blog posts, research papers, conference talks and other work authored by a lot of people:

- Agner Fog
- Daniel Lemire
- Wojciech Muła
- Malte Skarupke
- Matt Kulukundis
- Travis Downs
- Igor Ostrovsky
- Steven Pigeon
- Denis Bakhvalov
- Kazushige Goto
- Robert van de Geijn
- Oleksandr Bacherikov

Release date: fall 2021

### Part II: Parallel Algorithms

Concurrency, models of parallelism, green threads and runtimes, cache coherence, synchronization primitives, OpenMP, reductions, scans, list ranking and graph algorithms, lock-free data structures, heterogeneous computing, CUDA, kernels, warps, blocks, matrix multiplication and sorting.

Release date: early 2022

### Part III: Distributed Computing

Communication-constrained algorithms, message passing, actor model, partitioning, MapReduce, consistency and reliability at scale, storage, compression, scheduling and cloud computing, distributed deep learning.

Release date: ???

### Part IV: Compilers and Domain-Specific Architectures

LLVM IR, main optimization techniques from the dragon book, JIT-compilation, Cython, JAX, Numba, Julia, OpenCL, DPC++ and oneAPI, XLA, FPGAs and Verilog, ASICs, TPUs and other AI accelerators.

Release date: ???

### Disclaimer: Technology Choices

The examples in this book use C++, GCC, x86-64, CUDA and Spark, although the underlying principles we aim to convey are not specific to them.

To clear my conscience, I'm not happy with any of these choices: these technologies just happen to be the most widespread and stable at the moment, and thus more helpful for the reader. I would have respectively picked C / Rust, LLVM, arm, OpenCL and Dask; maybe there will be a 2nd edition in which some of the tech stack is changed.
