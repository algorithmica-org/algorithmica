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

<!--

### FAQ

**Release date.**

There are also future parts (see below).

As of March 2nd 2022, the first part is 70-80% complete.

**Fixing errors.** If you spot an error, please create an issue on GitHub or, preferably, fix it right away (the pencil icon on the top-right).

**Pre-ordering / financially supporting the book.**

Until I find.

The best way you can help is to share the articles on link aggregation.

In either case, the book will always be available online in full version. "pay what you want" hard copy.

**Translations.** As the book. The website has a functionality.

Italian and Chinese (and I will personally translate at least some of it in my native Russian).

However, you are encouraged to make your translation. I'd appreciate it if and also sent me the link to the translation.

**"Translating" the Russian version.** The articles at [ru.algorithmica.org/cs/](https://ru.algorithmica.org/cs/) are not about advanced performance engineering but mostly about classical computer science algorithms, targeted towards competitive programming audience.

They are undergrad-level, and most of the information there is not unique in other placed on the internet — e. g. the similar-spirited [cp-algorithms.com](https://cp-algorithms.com/).

-->

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
 1.4. When to Optimize
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
 4.4. Contract Programming
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
 5.6. Getting Accurate Results
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
(9.13. Memory Management)
9. RAM & CPU Caches
 9.1. Memory Bandwidth
 9.2. Memory Latency
 9.3. Cache Lines
 9.4. Memory Sharing
 9.5. Memory-Level Parallelism
 9.6. Prefetching
 9.7. Alignment and Packing
 9.8. Pointer Alternatives
 9.9. Cache Associativity
 9.10. Memory Paging
 9.11. AoS and SoA
10. SIMD Parallelism
 10.1. Intrinsics and Vector Types
 10.2. Loading and Writing Data
 10.3. Sums and Other Reductions
 10.4. Masking and Blending
 10.5. In-Register Shuffles
 10.6. Auto-Vectorization
11. Algorithm Case Studies
 11.1. Binary GCD
(11.2. Prime Number Sieves)
 11.3. Integer Factorization
 11.4. Logistic Regression
 11.5. Big Integers & Karatsuba Algorithm
 11.6. Fast Fourier Transform
 11.7. Number-Theoretic Transform
 11.8. Argmin with SIMD
 11.9. Prefix Sum with SIMD
 11.10. Reading and Writing Integers
(11.11. Reading and Writing Floats)
(11.12. String Searching)
 11.13. Sorting
 11.14. Matrix Multiplication
12. Data Structure Case Studies
 12.1. Binary Search
 12.2. Static B-Trees
 12.3. Segment Trees
(12.4. Search Trees)
(12.5. Range Minimum Query)
 12.6. Hash Tables
(12.7. Bitmaps)
(12.8. Probabilistic Filters)
```

Among cool things that we will speed up:

- 2x faster GCD (compared to `std::gcd`)
- 8-15x faster binary search (compared to `std::lower_bound`)
- 5-10x faster segment trees (compared to Fenwick trees)
- 5x faster hash tables (compared to `std::unordered_map`)
- 2x faster popcount (compared to repeatedly calling `popcnt`)
- 2x faster parsing series of integers (compared to `scanf`)
- ?x faster sorting (compared to `std::sort`)
- 2x faster sum (compared to `std::accumulate`)
- 2-3x faster prefix sum (compared to naive implementation)
- 10x faster argmin (compared to naive implementation)
- 10x faster array searching (compared to `std::find`)
- 100x faster matrix multiplication (compared to "for-for-for")
- optimal word-size integer factorization (~0.4ms per 60-bit integer)
- optimal Karatsuba Algorithm
- optimal FFT

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
- [Georg Sauthoff](https://gms.tf/)
- [Marshall Lochbaum](https://mlochbaum.github.io/publications.html)
- [ridiculous_fish](https://ridiculousfish.com/blog/)
- [Creel](https://www.youtube.com/c/WhatsACreel)

Volume: 450-600 pages  
Release date: Q2 2022

### Part II: Parallel Algorithms

Concurrency, models of parallelism, green threads and concurrent runtimes, cache coherence, synchronization primitives, OpenMP, reductions, scans, list ranking and graph algorithms, lock-free data structures, heterogeneous computing, CUDA, kernels, warps, blocks, matrix multiplication and sorting.

Volume: 150-200 pages  
Release date: 2023?

### Part III: Distributed Computing

Communication-constrained algorithms, message passing, actor model, partitioning, MapReduce, consistency and reliability at scale, storage, compression, scheduling and cloud computing, distributed deep learning.

Release date: ??? (more likely to be completed than not)

### Part IV: Compilers and Domain-Specific Architectures

LLVM IR, compiler optimizations, JIT-compilation, Cython, JAX, Numba, Julia, OpenCL, DPC++ and oneAPI, XLA,  Verilog, FPGAs, ASICs, TPUs and other AI accelerators.

Release date: ??? (less likely to be completed than not)

### Disclaimer: Technology Choices

The examples in this book use C++, GCC, x86-64, CUDA and Spark, although the underlying principles we aim to convey are not specific to them.

To clear my conscience, I'm not happy with any of these choices: these technologies just happen to be the most widespread and stable at the moment, and thus more helpful for the reader. I would have respectively picked C / Rust, LLVM, arm, OpenCL and Dask; maybe there will be a 2nd edition in which some of the tech stack is changed.
