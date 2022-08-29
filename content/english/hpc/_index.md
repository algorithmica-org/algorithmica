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

All book materials are [hosted on GitHub](https://github.com/algorithmica-org/algorithmica), with code in a [separate repository](https://github.com/sslotin/scmm-code). This isn't a collaborative project, but any contributions and feedback are very much welcome.

### FAQ

**Bug/typo fixes.** If you spot an error on any page, please do one of these — in the order of preference:

- fix it right away by either clicking on the pencil icon on the top right on any page (opens the [Prose](https://prose.io/) editor) or, more traditionally, by modifying the page directly on GitHub (the link to the source is also on the top right);
- create [an issue on GitHub](https://github.com/algorithmica-org/algorithmica/issues);
- [tell me](http://sereja.me/) about it directly;

or leave a comment on some other website where it is being discussed — I read most of [HackerNews](https://news.ycombinator.com/from?site=algorithmica.org), [CodeForces](https://codeforces.com/profile/sslotin), and [Twitter](https://twitter.com/sergey_slotin) threads where I'm tagged.

**Release date.** The book is split into several parts that I plan to finish sequentially with long breaks in-between. Part I, Performance Engineering, is ~75% complete as of March 2022 and will hopefully be >95% complete by this summer.

A "release" for an open-source book like this essentially means:

- finishing all essential sections and filling all the TODOs,
- mostly freezing the table of contents (except for the case studies),
- doing one final round of heavy copyediting (hopefully, with the help of a professional editor — I still haven’t figured out how commas work in English),
- drawing illustrations (I stole a lot of those that are currently displayed),
- making a print-optimized PDF and figuring out the best way to distribute it.

After that, I will mostly be fixing errors and only doing some minor edits reflecting the changes in technology or new algorithm advancements. The e-book/printed editions will most likely be sold on a "pay what you want" basis, and in any case, the web version will always be fully available online.

**Pre-ordering / financially supporting the book.** Due to my unfortunate citizenship and place of birth, you can't — that is, until I find a way that at the same time complies with international sanctions, doesn't sponsor [the war](https://en.wikipedia.org/wiki/2022_Russian_invasion_of_Ukraine), and won't put me in prison for tax evasion.

So, don't bother. If you want to support this book, just share it and help fix typos — that would be enough.

**Translations.** The website has a separate functionality for creating and managing translations — and I've already been contacted by some nice people willing to translate the book into Italian and Chinese (and I will personally translate at least some of it into my native Russian).

However, as the book is still evolving, it is probably not the best idea to start translating it at least until Part I is finished. That said, you are very much encouraged to make translations of any articles and publish them in your blogs — just send me the link so that we can merge it back when centralized translation starts.

**"Translating" the Russian version.** The articles hosted at [ru.algorithmica.org/cs/](https://ru.algorithmica.org/cs/) are not about advanced performance engineering but mostly about classical computer science algorithms — without discussing how to speed them up beyond asymptotic complexity. Most of the information there is not unique and already exists in English on some other places on the internet: for example, the similar-spirited [cp-algorithms.com](https://cp-algorithms.com/).

**Teaching performance engineering in colleges.** One of my goals for writing this book is to change the way computer science — algorithm design, to be more precise — is taught in colleges. Let me elaborate on that.

There are two highly impactful textbooks on which most computer science courses are built. Both are undoubtedly outstanding, but [one of them](https://en.wikipedia.org/wiki/The_Art_of_Computer_Programming) is 50 years old, and [the other](https://en.wikipedia.org/wiki/Introduction_to_Algorithms) is 30 years old, and [computers have changed a lot](/hpc/complexity/hardware) since then. Asymptotic complexity is not the sole deciding factor anymore. In modern practical algorithm design, you choose the approach that makes better use of different types of parallelism available in the hardware over the one that theoretically does fewer raw operations on galaxy-scale inputs.

And yet, the computer science curricula in most colleges completely ignore this shift. Although there are some great courses that aim to correct that — such as "[Performance Engineering of Software Systems](https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-172-performance-engineering-of-software-systems-fall-2018/)" from MIT, "[Programming Parallel Computers](https://ppc.cs.aalto.fi/)" from Aalto University, and some non-academic ones like Denis Bakhvalov's "[Performance Ninja](https://github.com/dendibakh/perf-ninja)" — most computer science graduates still treat modern hardware like something from the 1990s.

What I really want to achieve is that performance engineering becomes taught right after introduction to algorithms. Writing the first comprehensive textbook on the subject is a large part of it, and this is why I rush to finish it by the summer so that the colleges can pick it up in the next academic year. But creating a new course requires more than that: you need a balanced curriculum, course infrastructure, lecture slides, lab assignments… so for some time after finishing the main book, I will be working on course materials and tools for *teaching* performance engineering — and I'm looking forward to collaborating with other people who want to make it a reality as well.

<!--

Back then, you lived on the promise that Moore's law do the rest — and you'd mostly be right — but today we've hit the capacity of what a single CPU core can do.

The next thing is to create infrastructure, which .

I want it to be a book that CS students read after they've read 
TAOCP and CLRS.

There are good endeavors, such as,, and also, but these are more of an exception, and are also not deep enough to get people to the edge.

I've created courses from scratch in the past. I've already received, and I'm looking forward to collaborating more. Which is one of the reasons I rush to finish it by summer — so that colleges can pick up on the idea.

Competitive programming is, in my opinion, misguided. They are doing useless things, but they are good at doing wrong things, and the performance engineering community should learn from them.

-->

### Part I: Performance Engineering

The first part covers the basics of computer architecture and optimization of single-threaded algorithms.

It walks through the main CPU optimization topics such as caching, SIMD, and pipelining, and provides brief examples in C++, followed by large case studies where we usually achieve a significant speedup over some STL algorithm or data structure.

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
 1.3. Loops and Conditionals
 1.4. Functions and Recursion
 1.5. Indirect Branching
 1.6. Machine Code Layout
 1.7. System Calls
 1.8. Virtualization
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
 10.2. Moving Data
 10.3. Reductions
 10.4. Masking and Blending
 10.5. In-Register Shuffles
 10.6. Auto-Vectorization and SPMD
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
 11.10. Reading Decimal Integers
 11.11. Writing Decimal Integers
(11.12. Reading and Writing Floats)
(11.13. String Searching)
 11.14. Sorting
 11.15. Matrix Multiplication
12. Data Structure Case Studies
 12.1. Binary Search
 12.2. Static B-Trees
(12.3. Search Trees)
 12.4. Segment Trees
(12.5. Tries)
(12.6. Range Minimum Query)
 12.7. Hash Tables
(12.8. Bitmaps)
(12.9. Probabilistic Filters)
```

Among the cool things that we will speed up:

- 2x faster GCD (compared to `std::gcd`)
- 8-15x faster binary search (compared to `std::lower_bound`)
- 5-10x faster segment trees (compared to Fenwick trees)
- 5x faster hash tables (compared to `std::unordered_map`)
- 2x faster popcount (compared to repeatedly calling `popcnt`)
- 35x faster parsing series of integers (compared to `scanf`)
- ?x faster sorting (compared to `std::sort`)
- 2x faster sum (compared to `std::accumulate`)
- 2-3x faster prefix sum (compared to naive implementation)
- 10x faster argmin (compared to naive implementation)
- 10x faster array searching (compared to `std::find`)
- 15x faster search tree (compared to `std::set`)
- 100x faster matrix multiplication (compared to "for-for-for")
- optimal word-size integer factorization (~0.4ms per 60-bit integer)
- optimal Karatsuba Algorithm
- optimal FFT

Volume: 450-600 pages  
Release date: Q3 2022

### Part II: Parallel Algorithms

Concurrency, models of parallelism, context switching, green threads, concurrent runtimes, cache coherence, synchronization primitives, OpenMP, reductions, scans, list ranking, graph algorithms, lock-free data structures, heterogeneous computing, CUDA, kernels, warps, blocks, matrix multiplication, sorting.

Volume: 150-200 pages  
Release date: 2023-2024?

### Part III: Distributed Computing

<!-- (I might need some help from here on.) -->

Metworking, message passing, actor model, communication-constrained algorithms, distributed primitives, all-reduce, MapReduce, stream processing, query planning, storage, sharding, compression, distributed databases, consistency, reliability, scheduling, workflow engines, cloud computing.

Release date: ??? (more likely to be completed than not)

### Part IV: Software & Hardware

<!-- (TODO: come up with a better title — one that emphasizes that this part is mainly about the software-hardware boundary and not PL/IC design.) -->

LLVM IR, compiler optimizations & back-end, interpreters, JIT-compilation, Cython, JAX, Numba, Julia, OpenCL, DPC++, oneAPI, XLA, (basic) Verilog, FPGAs, ASICs, TPUs and other AI accelerators.

Release date: ??? (less likely to be completed than not)

### Acknowledgements

The book is largely based on blog posts, research papers, conference talks, and other work authored by a lot of people:

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
- [Danila Kutenin](https://danlark.org/author/kutdanila/)
- [Ivica Bogosavljević](https://johnysswlab.com/author/ibogi/)
- [Matt Pharr](https://pharr.org/matt/)
- [Jan Wassenberg](https://research.google/people/JanWassenberg/)
- [Marshall Lochbaum](https://mlochbaum.github.io/publications.html)
- [Pavel Zemtsov](https://pzemtsov.github.io/)
- [Gustavo Duarte](https://manybutfinite.com/)
- [Nyaan](https://nyaannyaan.github.io/library/)
- [Nayuki](https://www.nayuki.io/category/programming)
- [Konstantin](http://const.me/)
- [InstLatX64](https://twitter.com/InstLatX64)
- [ridiculous_fish](https://ridiculousfish.com/blog/)
- [Z boson](https://stackoverflow.com/users/2542702/z-boson)
- [Creel](https://www.youtube.com/c/WhatsACreel)

### Disclaimer: Technology Choices

The examples in this book use C++, GCC, x86-64, CUDA, and Spark, although the underlying principles conveyed are not specific to them.

To clear my conscience, I'm not happy with any of these choices: these technologies just happen to be the most widespread and stable at the moment and thus more helpful to the reader. I would have respectively picked C / Rust / [Carbon?](https://github.com/carbon-language/carbon-lang), LLVM, arm, OpenCL, and Dask; maybe there will be a 2nd edition in which some of the tech stack is changed.
