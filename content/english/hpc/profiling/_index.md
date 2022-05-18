---
title: Profiling
aliases: [/hpc/analyzing-performance/profiling]
weight: 5
---

Staring at the source code or its assembly is a popular, but not the most effective way of finding performance issues. When the performance doesn't meet your expectations, you can identify the root cause much faster using one of the special program analysis tools collectively called *profilers*. 

There are many different types of profilers. I like to think about them by analogy of how physicists and other natural scientists approach studying small things, picking the right tool depending on the required level of precision:

- When objects are on a micrometer scale, they use optical microscopes.
- When objects are on a nanometer scale, and light no longer interacts with them, they use electron microscopes.
- When objects are smaller than that (e.g., the insides of an atom), they resort to theories and assumptions about how things work (and test these assumptions using intricate and indirect experiments).

Similarly, there are three main profiling techniques, each operating by its own principles, having distinct areas of applicability, and allowing for different levels of precision:

- [Instrumentation](instrumentation) lets you time the program as a whole or by parts and count specific events you are interested in.
- [Statistical profiling](events) lets you go down to the assembly level and track various *hardware events* such as branch mispredictions or cache misses, which are critical for performance.
- [Program simulation](mca) lets you go down to the individual cycle level and look into what is happening inside the CPU on each cycle when it is executing a small assembly snippet.

Practical algorithm design can be very much considered an empirical field too. We largely rely on the same experimental methods, although this is not because we don't know some of the fundamental secrets of nature but mostly because modern computers are just too complex to analyze — besides, this is also true that we, regular software engineers, can't know some of the details because of IP protection from hardware companies (in fact, considering that the most accurate x86 instruction tables are [reverse-engineered](https://arxiv.org/pdf/1810.04610.pdf), there is a reason to believe that Intel doesn't know these details themselves).

In this chapter, we will study these three key profiling methods, as well as some time-tested practices for managing computational experiments involving performance evaluation.
