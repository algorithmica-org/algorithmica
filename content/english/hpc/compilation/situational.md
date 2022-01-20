---
title: Situational Optimizations
weight: 3
---

Generally, you always want to specify the exact platform you are running and turn on `-O3`, but other optimizations, like the ones discussed [in the previous section](../assembly), are far more situational and require some input from the programmer.

**Loop unrolling** is disabled by default, unless the loop takes a small constant number of iterations known at compile time (in which case it will be replaced with a completely jump-free repeated sequence of instructions). It can be enabled with `-funroll-loops` flag, which will unroll all loops whose number of iterations can be determined at compile time or upon entry to the loop.

You can also use a pragma to target a specific loop:

```c++
#pragma GCC unroll 4
for (int i = 0; i < n; i++) {
    // ...
}
```

Loop unrolling makes binary larger, and may or may not make it run faster. Don't use it fanatically.

**Likeliness of branches** can be hinted by `[[likely]]` and `[[unlikely]]` attributes in ifs and switches:

```c++
int factorial(int n) {
    if (n > 1) [[likely]]
        return n * factorial(n - 1);
    else [[unlikely]]
        return 1;
}
```

This is a new feature that only appeared in C++20. Before that, there were GCC-specific `likely` and `unlikely` macros similarly used to wrap condition expressions:

```c++
int factorial(int n) {
    if (likely(n > 1))
        return n * factorial(n - 1);
    else
        return 1;
}
```

What it usually does is it swaps the branches so that the more likely one goes immediately after jump (recall that "don't jump" branch is taken by default). The performance gain is usually rather small, because for most hot spots hardware branch prediction works just fine.

**Inlining** is best left for the compiler to decide, but you can influence it with `inline` keyword:

```c++
inline int square(int x) {
    return x * x;
}
```

The hint may be ignored though if the compiler thinks that the performance gains are not be worth it. You can force inlining in GCC by adding `always_inline` attribute:

```c++
#define FORCE_INLINE inline __attribute__((always_inline))
```

There are many other cases like this when you need to point the compiler in the right direction, but we will get to them later when they become more relevant.
