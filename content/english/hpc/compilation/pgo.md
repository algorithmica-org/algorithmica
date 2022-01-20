---
title: Profile-Guided Optimization
weight: 5
---

Adding all this metadata to the source code is tedious. People already hate writing C++ even without having to do it.

It is also not always obvious whether certain optimizations are beneficial or not. To make a decision about branch reordering, inlining or unrolling, we need answers to questions like these:

- How often is this branch taken?
- How often is this function called?
- What is the average number of iterations in this loop?

Luckily for us, there is a way to provide this real-world information automatically.

*Profile-guided optimization* (PGO, also called "pogo" because it's easier and more fun to pronounce) is a technique that uses profiling data to improve performance beyond what can be achieved with just static analysis. In a nutshell, it involves adding timers and counters to the points of interest in the program, compiling and running it on real data, and then compiling it again, but this time supplying additional information from the test run.

The whole process is automated by modern compilers. For example, the `-fprofile-generate` flag will let GCC instrument the program with profiling code:

```
g++ -fprofile-generate [other flags] source.cc -o binary
```

After we run the program — preferably on input that is as representative of real use case as possible — it will create a bunch of `*.gcda` files that contain log data for the test run, after which we can rebuild the program, but now adding the `-fprofile-use` flag:

```
g++ -fprofile-use [other flags] source.cc -o binary
```

It usually improves performance by 10-20% for large codebases, and for this reason it is commonly included in the build process of performance-critical projects. One more reason to invest in solid benchmarking code.

We will study how it works more deeply in the [next chapter](../../profiling).
