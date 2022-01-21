---
title: Summary
weight: 99
ignoreIndexing: true
draft: true
---

Now we have enough information to summarize what we've learned.

Loop unrolling.

Here is a checklist (from easiest to hardest):

0. Turn on optimization (`-march=native`, `-O3`, `-ffast-math`, `-funroll-loops`)
1. Determine whether the algorithm is memory-bound or compute-bound.
2. Blocking: try to split data in parts that fit cache
3. Memory access patterns: try to linearize every reads
4. Prefetching: if access pattern is not well predictable, or port is free, add a prefetching step
5. Branching: remove branching
6. Loop Unrolling: `#pragma GCC unroll n`
7. Data Dependencies: consult and instruction table or llvm-mca
8. SIMD: simplify a loop
9. Arithmetic: use smallest type available and turn on `-ffast-math`
10. Temporal locality
11. Allocations
12. Profile stuff