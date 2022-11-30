---
title: Flags and Targets
weight: 2
published: true
---

The first step of getting high performance from the compiler is to ask for it, which is done with over a hundred different compiler options, attributes, and pragmas.

### Optimization Levels

There are 4 *and a half* main levels of optimization for speed in GCC:

- `-O0` is the default one that does no optimizations (although, in a sense, it does optimize: for compilation time).
- `-O1` (also aliased as `-O`) does a few "low-hanging fruit" optimizations, almost not affecting the compilation time.
- `-O2` enables all optimizations that are known to have little to no negative side effects and take a reasonable time to complete (this is what most projects use for production builds).
- `-O3` does very aggressive optimization, enabling almost all *correct* optimizations implemented in GCC.
- `-Ofast` does everything in `-O3`, plus a few more optimizations flags that may break strict standard compliance, but not in a way that would be critical for most applications (e.g., floating-point operations may be rearranged so that the result is off by a few bits in the mantissa).

There are also many other optimization flags that are not included even in `-Ofast`, because they are very situational, and enabling them by default is more likely to hurt performance rather than improve it — we will talk about some of them in [the next section](../situational).

### Specifying Targets

The next thing you may want to do is to tell the compiler more about the computer(s) this code is supposed to be run on: the smaller the set of platforms is, the better. By default, it will generate binaries that can run on any relatively new (>2000) x86 CPU. The simplest way to narrow it down is to pass `-march` flag to specify the exact microarchitecture: `-march=haswell`. If you are compiling on the same computer that will run the binary, you can use `-march=native` for auto-detection.

The instruction sets are generally backward-compatible, so it is often enough to just use the name of the oldest microarchitecture you need to support. A more robust approach is to list specific features that the CPU is guaranteed to have: `-mavx2`, `-mpopcnt`. When you just want to *tune* the program for a particular machine without using any instructions that may crash it on incompatible CPUs, you can use the `-mtune` flag (by default `-march=x` also implies `-mtune=x`).

These options can also be specified for a compilation unit with pragmas instead of compilation flags:

```c++
#pragma GCC optimize("O3")
#pragma GCC target("avx2")
```

This is useful when you need to optimize a single high-performance procedure without increasing the build time for the entire project.

### Multiversioned Functions

Sometimes you may also want to provide several architecture-specific implementations in a single library. You can use attribute-based syntax to select between multiversioned functions automatically during compile time:

```c++
__attribute__(( target("default") )) // fallback implementation
int popcnt(int x) {
    int s = 0;
    for (int i = 0; i < 32; i++)
        s += (x>>i&1);
    return s;
}

__attribute__(( target("popcnt") )) // used if popcnt flag is enabled
int popcnt(int x) {
    return __builtin_popcount(x);
}
```

In Clang, you can't use pragmas to set target and optimization flags from the source code, but you can use attributes the same way as in GCC.
