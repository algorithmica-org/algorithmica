---
title: Auto-Vectorization
weight: 10
---

Most often, SIMD is used for "embarrassingly parallel" computations: the ones where all you do is apply some elementwise function to all elements of an array and write it back somewhere else. In this setting, you don't even need to know how SIMD works: the compiler is perfectly capable of optimizing such loops by itself. All you need to know is that such optimization exists and yields a 5-10x speedup.

But most computations are not like that, and even the loops that seem straightforward to vectorize are often not optimized because of some tricky technical nuances. In this section, we will discuss how to assist the compiler in vectorization and walk through some more complicated patterns of using SIMD.

## Assisting Autovectorization

Of course, the preferred way of using SIMD is by the means of autovectorization. Whenever you can, you should always stick with the scalar code for its simplicity and maintainability. But, [as in many other cases](/hpc/analyzing-performance/compilation), compiler often needs some additional input from the programmer, who may know a little bit more about the problem.

Consider the "a+b" example:

```c++
void sum(int a[], int b[], int c[], int n) {
    for (int i = 0; i < n; i++)
        c[i] = a[i] + b[i];
}
```

This function can't be replaced with the vectorized variant automatically. Why?

First, vectorization here is not always technically correct. Assuming that `a[]` and `c[]` intersect in a way that their beginnings differ by a single position — because who knows, maybe the programmer wanted to calculate the Fibonacci sequence through a convolution this way. In this case, the data in the SIMD blocks will intersect, and the observed behavior will differ from the one in the scalar case.

Second, we don't know anything about the alignment of these arrays, and we can lose some performance here by using unaligned instructions.

On high (`-O3`) levels of optimization, when the compiler suspects that the function may be used for large cycles, it generates two implementation variants — a SIMDized and a "safe" one — and inserts runtime checks to choose between the two.

To avoid these runtime checks, we can tell compiler that we are sure that nothing will break. One way to do this is using the `__restrict__` keyword:

```cpp
void add(int * __restrict__ a, const int * __restrict__ b, int n) {
    for (int i = 0; i < n; i++)
        a[i] += b[i];
}
```

The other, specific to SIMD, is the "ignore vector dependencies" pragma, which is the way to tell compiler that we are sure there are no dependencies between the loop iterations:

```c++
#pragma GCC ivdep
for (int i = 0; i < n; i++)
    // ...
```

There are [many other ways](https://software.intel.com/sites/default/files/m/4/8/8/2/a/31848-CompilerAutovectorizationGuide.pdf) of hinting compiler what we meant exactly, but in especially complex cases — when inside the loop there are a lot of branches or some functions are called — it is easier to go down to the intrinsics level and write it yourself.

`std::assume_aligned`, specifiers. This is useful for SIMD instructions that need memory alignment guarantees
