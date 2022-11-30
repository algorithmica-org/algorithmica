---
title: Program Simulation
weight: 3
---

The last approach to profiling (or rather a group of them) is not to gather the data by actually running the program but to analyze what should happen by *simulating* it with specialized tools.

<!--

There are many subcategories of such profilers, differing in which aspect of computation is simulated, but the one we are going to focus on in this section is *machine code analyzers*.

The last approach (or rather a group of them) is not to gather the data by actually running the program, but to analyze what should happen by *simulating* it with specialized tools, which roughly fall into two categories.

-->

There are many subcategories of such profilers, differing in which aspect of computation is simulated. In this article, we are going to focus on [caching](/hpc/cpu-cache) and [branch prediction](/hpc/pipelining/branching), and use [Cachegrind](https://valgrind.org/docs/manual/cg-manual.html) for that, which is a profiling-oriented part of [Valgrind](https://valgrind.org/), a well-established tool for memory leak detection and memory debugging in general.

### Profiling with Cachegrind

Cachegrind essentially inspects the binary for "interesting" instructions — that perform memory reads / writes and conditional / indirect jumps — and replaces them with code that simulates corresponding hardware operations using software data structures. It therefore doesn't need access to the source code and can work with already compiled programs, and can be run on any program like this:

```bash
valgrind --tool=cachegrind --branch-sim=yes ./run
#       also simulate branch prediction ^   ^ any command, not necessarily one process
```

It instruments all involved binaries, runs them, and outputs a summary similar to [perf stat](../events):

```
I   refs:      483,664,426
I1  misses:          1,858
LLi misses:          1,788
I1  miss rate:        0.00%
LLi miss rate:        0.00%

D   refs:      115,204,359  (88,016,970 rd   + 27,187,389 wr)
D1  misses:      9,722,664  ( 9,656,463 rd   +     66,201 wr)
LLd misses:         72,587  (     8,496 rd   +     64,091 wr)
D1  miss rate:         8.4% (      11.0%     +        0.2%  )
LLd miss rate:         0.1% (       0.0%     +        0.2%  )

LL refs:         9,724,522  ( 9,658,321 rd   +     66,201 wr)
LL misses:          74,375  (    10,284 rd   +     64,091 wr)
LL miss rate:          0.0% (       0.0%     +        0.2%  )

Branches:       90,575,071  (88,569,738 cond +  2,005,333 ind)
Mispredicts:    19,922,564  (19,921,919 cond +        645 ind)
Mispred rate:         22.0% (      22.5%     +        0.0%   )
```

We've fed Cachegrind exactly the same example code as in [the previous section](../events): we create an array of a million random integers, sort it, and then perform a million binary searches on it. Cachegrind shows roughly the same numbers as perf does, except that that perf's measured numbers of memory reads and branches are slightly inflated due to [speculative execution](/hpc/pipelining): they really happen in hardware and thus increment hardware counters, but are discarded and don't affect actual performance, and thus ignored in the simulation.

Cachegrind only models the first (`D1` for data, `I1` for instructions) and the last (`LL`, unified) levels of cache, the characteristics of which are inferred from the system. It doesn't limit you in any way as you can also set them from the command line, e g., to model the L2 cache: `--LL=<size>,<associativity>,<line size>`.

It seems like it only slowed down our program so far and hasn't provided us any information that `perf stat` couldn't. To get more out of it than just the summary info, we can inspect a special file with profiling info, which it dumps by default in the same directory named as `cachegrind.out.<pid>`. It is human-readable, but is expected to be read via the `cg_annotate` command:

```bash
cg_annotate cachegrind.out.4159404 --show=Dr,D1mr,DLmr,Bc,Bcm
#                                    ^ we are only interested in data reads and branches
```

First it shows the parameters that were used during the run, including the characteristics of the cache system:

```
I1 cache:         32768 B, 64 B, 8-way associative
D1 cache:         32768 B, 64 B, 8-way associative
LL cache:         8388608 B, 64 B, direct-mapped
```

It didn't get the L3 cache quite right: it is not unified (8M in total, but a single core only sees 4M) and also 16-way associative, but we will ignore that for now.

Next, it outputs a per-function summary similar to `perf report`:

```
Dr         D1mr      DLmr Bc         Bcm         file:function
--------------------------------------------------------------------------------
19,951,476 8,985,458    3 41,902,938 11,005,530  ???:query()
24,832,125   585,982   65 24,712,356  7,689,480  ???:void std::__introsort_loop<...>
16,000,000        60    3  9,935,484    129,044  ???:random_r
18,000,000         2    1  6,000,000          1  ???:random
 4,690,248    61,999   17  5,690,241  1,081,230  ???:setup()
 2,000,000         0    0          0          0  ???:rand
```

You can see there are a lot of branch mispredicts in the sorting stage, and also a lot of both L1 cache misses and branch mispredicts during binary searching. We couldn't get this information with perf — it would only tell use these counts for the whole program.

Another great feature that Cachegrind has is the line-by-line annotation of source code. For that, you need to compile the program with debug information (`-g`) and either explicitly tell `cg_annotate` which source files to annotate or just pass the `--auto=yes` option so that it annotates everything it can reach (including the standard library source code).

The whole source-to-analysis process would therefore go like this:

```bash
g++ -O3 -g sort-and-search.cc -o run
valgrind --tool=cachegrind --branch-sim=yes --cachegrind-out-file=cachegrind.out ./run
cg_annotate cachegrind.out --auto=yes --show=Dr,D1mr,DLmr,Bc,Bcm
```

Since the glibc implementations are not the most readable, for exposition purposes, we replace `lower_bound` with our own binary search, which will be annotated like this:

```c++
Dr         D1mr      DLmr Bc         Bcm       
         .         .    .          .         .  int binary_search(int x) {
         0         0    0          0         0      int l = 0, r = n - 1;
         0         0    0 20,951,468 1,031,609      while (l < r) {
         0         0    0          0         0          int m = (l + r) / 2;
19,951,468 8,991,917   63 19,951,468 9,973,904          if (a[m] >= x)
         .         .    .          .         .              r = m;
         .         .    .          .         .          else
         0         0    0          0         0              l = m + 1;
         .         .    .          .         .      }
         .         .    .          .         .      return l;
         .         .    .          .         .  }
```

Unfortunately, Cachegrind only tracks memory accesses and branches. When the bottleneck is caused by something else, we need [other simulation tools](../mca).
