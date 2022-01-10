---
title: Benchmarking
weight: 6
---


## Algorithm Design as an Empirical Field

I like to think about these three profiling methods by an analogy of how natural scientists approach studying small things, picking just the right tool based on the required level of precision:

- When objects are on a micrometer scale, they use optical microscopes. (`time`, `perf stat`, instrumentation)
- When objects are on a nanometer scale and light no longer interacts with them, they use electron microscopes. (`perf record` / `perf report`, heatmaps)
- When objects are smaller than that (the insides of an atom), they resort to theories and assumptions about how things work. (`llvm-mca`, `cachegrind`, staring at assembly)

For practical algorithm design, we use the same empirical methods, although this is not because we don't know some of the fundamental secrets of nature, but mostly because modern computers are too complex to analyze — besides, this is also true that we, regular software engineers, can't know some of the details because of IP protection from hardware companies. In fact, considering that the most accurate x86 instruction tables are [reverse-engineered](https://arxiv.org/pdf/1810.04610.pdf), there is a reason to believe that Intel doesn't know these details themselves.

In this setting, it is a good idea to follow the same time-tested practices that people use in other empirical fields.

### Managing Experiments

If you do it correctly, working on improving performance should resemble a loop:

1. run the program and collect metrics,
2. figure out where the bottleneck is,
3. remove the bottleneck and go to step 1.

The shorter this loop is, the faster you will iterate. Here are some hints on how to set up your environment to achieve this (you can find many examples in the [code repo](https://github.com/sslotin/ahm-code) for this book):

- Separate all testing and analytics code from the implementation of the algorithm itself, and also different implementations from each other. In C/C++, you can do this by creating a single header file (e. g. `matmul.hh`) with a function interface and the code for its benchmarking in `main`, and many implementation files for each algorithm version (`v1.cc`, `v2.cc`, etc.) that all include that single header file.
- To speed up builds and reruns, create a Makefile or just a bunch of small scripts that calculate the statistics you may need.
- To speed up high-level analytics, create a Jupyter notebook where you put small scripts and do all the plots. You can also put build scripts there if you feel like it.
- To put numbers in perspective, use statistics like "ns per query" or "cycles per byte" instead of wall clock whenever it is applicable. When you start to approach very high levels of performance, it makes sense to calculate what the theoretically maximal performance is and start thinking about your algorithm performance as a fraction of it.

Also, make the dataset as representing of your real use case as possible, and reach an agreement with people on the procedure of benchmarking. This is especially important for data processing algorithms and data structures: most sorting algorithms perform differently depending on the input, hash tables perform differently with different distributions of keys.

https://github.com/google/benchmark

### Interleaving

Similar to how Americans report pre-tax salary, Americans use non-PPP-adjusted stats, attention-seeking startups report revenue instead of profit, performance engineers report the best version of benchmark if not stated otherwise.

I have never seen people do that though. It makes most difference when comparing branchy and branch-free algorithms.

People report things they like to report and leave out the things they don't.
