---
title: Situational Optimizations
weight: 3
---

<!--

Generally, you always want to specify the exact platform you are running and turn on `-O3`, but other optimizations, like the ones discussed [in the previous section](../assembly), are far more situational and require some input from the programmer.

-->

Most compiler optimizations enabled by `-O2` and `-O3` are guaranteed to either improve or at least not seriously hurt performance. Those that aren't included in `-O3` are either not strictly standard-compliant, or highly circumstantial and require some additional input from the programmer to help decide whether using them is beneficial.

Let's discuss the most frequently used ones that we've also previously covered in this book.

### Loop Unrolling

[Loop unrolling](/hpc/architecture/loops#loop-unrolling) is disabled by default, unless the loop takes a small constant number of iterations known at compile time — in which case it will be replaced with a completely jump-free, repeated sequence of instructions. It can be enabled globally with the `-funroll-loops` flag, which will unroll all loops whose number of iterations can be determined at compile time or upon entry to the loop.

You can also use a pragma to target a specific loop:

```c++
#pragma GCC unroll 4
for (int i = 0; i < n; i++) {
    // ...
}
```

Loop unrolling makes binary larger, and may or may not make it run faster. Don't use it fanatically.

### Function Inlining

[Inlining](/hpc/architecture/functions#inlining) is best left for the compiler to decide, but you can influence it with `inline` keyword:

```c++
inline int square(int x) {
    return x * x;
}
```

The hint may be ignored though if the compiler thinks that the potential performance gains are not worth it. You can force inlining by adding the `always_inline` attribute:

```c++
#define FORCE_INLINE inline __attribute__((always_inline))
```

There is also the `-finline-limit=n` option which lets you set a specific threshold on the size of inlined functions (in terms of the number of instructions). Its Clang equivalent is `-inline-threshold`.

### Likeliness of Branches

[Likeliness of branches](/hpc/architecture/layout#unequal-branches) can be hinted by `[[likely]]` and `[[unlikely]]` attributes in `if`-s and `switch`-es:

```c++
int factorial(int n) {
    if (n > 1) [[likely]]
        return n * factorial(n - 1);
    else [[unlikely]]
        return 1;
}
```

This is a new feature that only appeared in C++20. Before that, there were compiler-specific intrinsics similarly used to wrap condition expressions. The same example in older GCC:

```c++
int factorial(int n) {
    if (__builtin_expect(n > 1, 1))
        return n * factorial(n - 1);
    else
        return 1;
}
```

<!--
What it usually does is it swaps the branches so that the more likely one goes immediately after jump (recall that "don't jump" branch is taken by default). The performance gain is usually rather small, because for most hot spots hardware branch prediction works just fine.
-->

There are many other cases like this when you need to point the compiler in the right direction, but we will get to them later when they become more relevant.

### Profile-Guided Optimization

Adding all this metadata to the source code is tedious. People already hate writing C++ even without having to do it.

It is also not always obvious whether certain optimizations are beneficial or not. To make a decision about branch reordering, function inlining, or loop unrolling, we need answers to questions like these:

- How often is this branch taken?
- How often is this function called?
- What is the average number of iterations in this loop?

Luckily for us, there is a way to provide this real-world information automatically.

*Profile-guided optimization* (PGO, also called "pogo" because it's easier and more fun to pronounce) is a technique that uses [profiling data](/hpc/profiling) to improve performance beyond what can be achieved with just static analysis. In a nutshell, it involves adding timers and counters to the points of interest in the program, compiling and running it on real data, and then compiling it again, but this time supplying additional information from the test run.

The whole process is automated by modern compilers. For example, the `-fprofile-generate` flag will let GCC instrument the program with profiling code:

```
g++ -fprofile-generate [other flags] source.cc -o binary
```

After we run the program — preferably on input that is as representative of the real use case as possible — it will create a bunch of `*.gcda` files that contain log data for the test run, after which we can rebuild the program, but now adding the `-fprofile-use` flag:

```
g++ -fprofile-use [other flags] source.cc -o binary
```

It usually improves performance by 10-20% for large codebases, and for this reason it is commonly included in the build process of performance-critical projects. This is more reason to invest in solid benchmarking code.

<!--

We will study how profiling works more deeply in the [next chapter](../../profiling).

-->
