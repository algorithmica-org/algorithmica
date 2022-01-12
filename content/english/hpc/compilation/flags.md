---
title: Flags and Targets
weight: 2
---

The first step of getting high performance from the compiler is to ask for it.

There are 4 *and a half* main levels of optimization for speed in GCC:

- `-O0` is the default one that does no optimizations (although, in a sense, it does optimize: for compilation time).
- `-O1` (also aliased as `-O`) does a few "low-hanging fruit" optimizations almost not affecting the compilation time.
- `-O2` enables all optimizations that are known to have little to no negative side effects and take reasonable time to complete (this is what most projects use for production builds).
- `-O3` does very aggressive optimization enabling almost all *correct* optimizations implemented in GCC.
- `-Ofast` does everything in `-O3` as well as adds a few more optimizations flags that may break strict standard compliance (e. g. floating-point operations may be rearranged so that the result is off by a few bits of the mantissa).

The next thing you want to do is to tell the compiler more about the computer(s) this code is supposed to be run on: the smaller the set of platforms is, the better. By default it will generate binaries that can run on any relatively new (>2000) x86 CPU. The simplest way to narrow it down is to pass `-march` flag to specify the exact microarchitecture: `-march=haswell`. If you are compiling on the same computer that will run the binary, you can use `-march=native` for auto-detection.

The instruction sets are generally backwards-compatible, so it is often enough to use the name of the oldest microarchitecture you need to support, but a more robust approach is to list specific features that the CPU is guaranteed to have: `-mavx2`, `-mpopcount`. When you just want to tune a program for a particular machine without using any instructions that may break it on incompatible CPUs, you can use `-mtune` flag (by default `-march=x` also implies `-mtune=x`).

These options can also be specified for a compilation unit with pragmas instead of compilation flags:

```c++
#pragma GCC optimize("O3")
#pragma GCC target("avx2")
```

This is useful when you need to optimize a single high-performance procedure without increasing build time for the entire project.
