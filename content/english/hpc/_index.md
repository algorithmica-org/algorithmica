---
title: Algorithms for Modern Hardware
menuTitle: HPC
weight: 5
#authors:
#- Sergey Slotin
#created: "Feb 2021"
#date: 2021-09-16
noToc: true
---

This is an upcoming high performance computing book titled "Algorithms for Modern Hardware" by [Sergey Slotin](http://sereja.me/).

Its intended audience is everyone from performance engineers and practical algorithm researchers to undergraduate computer science students who have just finished an advanced algorithms course and want to learn more practical ways to speed up a program than by going from $O(n \log n)$ to $O(n \log \log n)$.

All materials are hosted on GitHub, with code in a [separate repository](https://github.com/sslotin/scmm-code). This isn't a collaborative project, but any contributions and feedback are very much welcome.

### Part I: Performance Engineering

The first part covers the basics of computer architecture and optimization of single-threaded algorithms.

It walks through the main CPU optimization topics such as caching, SIMD and pipelining, and provides brief examples in C++, followed by large case studies where we usually achieve a significant speedup over some STL algorithm or data structure.

Planned table of contents:

```
0. Preface
1. Complexity Models
 1.1. Modern Hardware
 1.2. Programming Languages
 1.3. Models of Computation
 1.4. Levels of Optimization
2. Computer Architecture
 1.1. Instruction Set Architectures
 1.2. Assembly Language
 1.2. Loops and Conditionals
 1.3. Functions and Recursion
 1.4. Indirect Branching
 1.5. Interrupts and System Calls
 1.6. Machine Code Layout
3. Instruction-Level Parallelism
 3.1. Pipeline Hazards
 3.2. The Cost of Branching
 3.3. Branchless Programming
 3.4. Instruction Tables
 3.5. Instruction Scheduling
 3.6. Throughput Computing
 3.7. Theoretical Performance Limits
4. Compilation
 4.1. Stages of Compilation
 4.2. Flags and Targets
 4.3. Situational Optimizations
 4.4. Contracts Programming
 4.5. Non-Zero-Cost Abstractions
 4.6. Compile-Time Computation
 4.7. Arithmetic Optimizations
 4.8. What Compilers Can and Can't Do
5. Profiling
 5.1. Instrumentation
 5.2. Statistical Profiling
 5.3. Program Simulation
 5.4. Machine Code Analyzers
 5.5. Benchmarking
6. Arithmetic
 6.1. Floating-Point Numbers
 6.2. Interval Arithmetic
 6.3. Newton's Method
 6.4. Fast Inverse Square Root
 6.5. Integers
 6.6. Integer Division
 6.7. Bit Manipulation
(6.8. Data Compression)
7. Number Theory
 7.1. Modular Inverse
 7.2. Montgomery Multiplication
(7.3. Finite Fields)
(7.4. Error Correction)
 7.5. Cryptography
 7.6. Hashing
 7.7. Random Number Generation
8. External Memory
 8.1. Memory Hierarchy
 8.2. Virtual Memory
 8.3. External Memory Model
 8.4. External Sorting
 8.5. List Ranking
 8.6. Eviction Policies
 8.7. Cache-Oblivious Algorithms
 8.8. Spacial and Temporal Locality
(8.9. B-Trees)
(8.10. Sublinear Algorithms)
9. RAM & CPU Caches
 9.1. Memory Bandwidth
 9.2. Memory Latency
 9.3. Cache Lines
 9.4. Data Alignment
 9.5. Structure Packing
 9.6. Pointer Alternatives
 9.7. Cache Associativity
 9.8. Memory Paging
 9.9. Memory-Level Parallelism
 9.10. Hardware Prefetching
 9.11. Software Prefetching
 9.12. AoS and SoA
(9.13. Memory Management)
10. SIMD Parallelism
 10.1. Using SIMD in C/C++
 10.2. Reductions
 10.3. Auto-Vectorization
 10.4. Data Twiddling
 10.5. SSE & AVX Cookbook
11. Algorithm Case Studies
 11.1. Binary GCD
(11.2. Prime Number Sieves)
 11.3. Integer Factorization
 11.4. Logistic Regression
 11.5. Big Integers & Karatsuba Algorithm
 11.6. Fast Fourier Transform
 11.7. Number-Theoretic Transform
 11.8. Argmin with SIMD
 11.9. Reading and Writing Integers
(11.10. Reading and Writing Floats)
(11.11. String Searching)
 11.12. Sorting
 11.13. Matrix Multiplication
12. Data Structure Case Studies
 12.1. Binary Search
 12.2. Dynamic Prefix Sum
(12.3. Ordered Trees)
(12.4. Range Minimum Query)
 12.5. Hash Tables
(12.6. Bitmaps)
(12.7. Probabilistic Filters)
```

Among cool things that we will speed up:

- 2x faster GCD (compared to `std::gcd`)
- 5x faster binary search (compared to `std::lower_bound`)
- 7x faster segment trees
- 5x faster hash tables (compared to `std::unordered_map`)
- ~~?x faster popcount~~
- 2x faster parsing series of integers (compared to `scanf`)
- ?x faster sorting (compared to `std::sort`)
- 2x faster sum (compared to `std::accumulate`)
- 100x faster matrix multiplication (compared to "for-for-for")
- optimal word-size integer factorization (~0.4ms per 60-bit integer)
- optimal Karatsuba Algorithm
- optimal FFT
- argmin at the speed of memory

This work is largely based on blog posts, research papers, conference talks and other work authored by a lot of people:

- [Agner Fog](https://agner.org/optimize/)
- [Daniel Lemire](https://lemire.me/en/#publications)
- [Andrei Alexandrescu](https://erdani.com/index.php/about/)
- [Chandler Carruth](https://twitter.com/chandlerc1024)
- [Wojciech Muła](http://0x80.pl/articles/index.html)
- [Malte Skarupke](https://probablydance.com/)
- [Travis Downs](https://travisdowns.github.io/)
- [Brendan Gregg](https://www.brendangregg.com/blog/index.html)
- [Andreas Abel](http://embedded.cs.uni-saarland.de/abel.php)
- [Jakob Kogler](https://cp-algorithms.com/)
- [Igor Ostrovsky](http://igoro.com/)
- [Steven Pigeon](https://hbfs.wordpress.com/)
- [Denis Bakhvalov](https://easyperf.net/notes/)
- [Paul Khuong](https://pvk.ca/)
- [Pat Morin](https://cglab.ca/~morin/)
- [Victor Eijkhout](https://www.tacc.utexas.edu/about/directory/victor-eijkhout)
- [Robert van de Geijn](https://www.cs.utexas.edu/~rvdg/)
- [Edmond Chow](https://www.cc.gatech.edu/~echow/)
- [Peter Cordes](https://stackoverflow.com/users/224132/peter-cordes)
- [Geoff Langdale](https://branchfree.org/)
- [Matt Kulukundis](https://twitter.com/JuvHarlequinKFM)
- [ridiculous_fish](https://ridiculousfish.com/blog/)
- [Creel](https://www.youtube.com/c/WhatsACreel)

Volume: 300-400 pages  
Release date: early 2022

### Part II: Parallel Algorithms

Concurrency, models of parallelism, green threads and runtimes, cache coherence, synchronization primitives, OpenMP, reductions, scans, list ranking and graph algorithms, lock-free data structures, heterogeneous computing, CUDA, kernels, warps, blocks, matrix multiplication and sorting.

Volume: 150-200 pages  
Release date: late 2022 / 2023?

### Part III: Distributed Computing

Communication-constrained algorithms, message passing, actor model, partitioning, MapReduce, consistency and reliability at scale, storage, compression, scheduling and cloud computing, distributed deep learning.

Release date: ???

### Part IV: Compilers and Domain-Specific Architectures

LLVM IR, main optimization techniques from the dragon book, JIT-compilation, Cython, JAX, Numba, Julia, OpenCL, DPC++ and oneAPI, XLA, FPGAs and Verilog, ASICs, TPUs and other AI accelerators.

Release date: ???

### Disclaimer: Technology Choices

The examples in this book use C++, GCC, x86-64, CUDA and Spark, although the underlying principles we aim to convey are not specific to them.

To clear my conscience, I'm not happy with any of these choices: these technologies just happen to be the most widespread and stable at the moment, and thus more helpful for the reader. I would have respectively picked C / Rust, LLVM, arm, OpenCL and Dask; maybe there will be a 2nd edition in which some of the tech stack is changed.
