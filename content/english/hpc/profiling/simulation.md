---
title: Simulation
weight: 3
draft: true
---

The last approach (or rather a group of them) is not to gather the data by actually running the program, but to analyze what should happen by *simulating* it with specialized tools, which roughly fall into two categories.

The first one is *memory profilers*. A particular example is `cachegrind`, which is a part of `valgrind`. It simulates all memory operations to assess memory performance down to the individual cache line level. Although they usually significantly slow down the program in the process, they can provide more information than just `perf` cache events.
