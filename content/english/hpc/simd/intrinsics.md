---
title: Intrinsics and Vector Types
aliases: [/hpc/simd/x86-simd]
weight: 1
---

The most low-level way to use SIMD is to use the assembly vector instructions directly — they aren't different from their scalar equivalents at all — but we are not going to do that. Instead, we will use *intrinsic* functions mapping to these instructions that are available in modern C/C++ compilers.

In this section, we will go through the basics of their syntax, and in the rest of this chapter, we will use them extensively to do things that are actually interesting.

## Setup

To use x86 intrinsics, we need to do a little groundwork.

First, we need to determine which extensions are supported by the hardware. On Linux, you can call `cat /proc/cpuinfo`, and on other platforms, you'd better go to [WikiChip](https://en.wikichip.org/wiki/WikiChip) and look it up there using the name of the CPU. In either case, there should be a `flags` section that lists the codes of all supported vector extensions.

There is also a special [CPUID](https://en.wikipedia.org/wiki/CPUID) assembly instruction that lets you query various information about the CPU, including the support of particular vector extensions. It is primarily used to get such information in runtime and avoid distributing a separate binary for each microarchitecture. Its output information is returned very densely in the form of feature masks, so compilers provide built-in methods to make sense of it. Here is an example:

```c++
#include <iostream>
using namespace std;

int main() {
    cout << __builtin_cpu_supports("sse") << endl;
    cout << __builtin_cpu_supports("sse2") << endl;
    cout << __builtin_cpu_supports("avx") << endl;
    cout << __builtin_cpu_supports("avx2") << endl;
    cout << __builtin_cpu_supports("avx512f") << endl;

    return 0;
}
```

Second, we need to include a header file that contains the subset of intrinsics we need. Similar to `<bits/stdc++.h>` in GCC, there is the `<x86intrin.h>` header that contains all of them, so we will just use that.

And last, we need to [tell the compiler](/hpc/compilation/flags) that the target CPU actually supports these extensions. This can be done either with `#pragma GCC target(...)` [as we did before](../), or with the `-march=...` flag in the compiler options. If you are compiling and running the code on the same machine, you can set `-march=native` to auto-detect the microarchitecture.

In all further code examples, assume that they begin with these lines:

```c++
#pragma GCC target("avx2")
#pragma GCC optimize("O3")

#include <x86intrin.h>
#include <bits/stdc++.h>

using namespace std;
```

We will focus on AVX2 and the previous SIMD extensions in this chapter, which should be available on 95% of all desktop and server computers, although the general principles transfer on AVX512, Arm Neon, and other SIMD architectures just as well.

### SIMD Registers

The most notable distinction between SIMD extensions is the support for wider registers:

- SSE (1999) added 16 128-bit registers called `xmm0` through `xmm15`.
- AVX (2011) added 16 256-bit registers called `ymm0` through `ymm15`.
- AVX512 (2017) added[^mask] 16 512-bit registers called `zmm0` through `zmm15`.

[^mask]: AVX512 also added 8 so-called *mask registers* named `k0` through `k7`, which are used for masking and blending data. We are not going to cover them and will mostly use AVX2 and previous standards.

As you can guess from the naming, and also from the fact that 512 bits already occupy a full cache line, x86 designers are not planning to add wider registers anytime soon.

C/C++ compilers implement special *vector types* that refer to the data stored in these registers:

- 128-bit `__m128`, `__m128d` and `__m128i` types for single-precision floating-point, double-precision floating-point and various integer data respectively;
- 256-bit `__m256`, `__m256d`, `__m256i`;
- 512-bit `__m512`, `__m512d`, `__m512i`.

Registers themselves can hold data of any kind: these types are only used for type checking. You can convert a vector variable to another vector type the same way you would normally convert any other type, and it won't cost you anything.

### SIMD Intrinsics

*Intrinsics* are just C-style functions that do something with these vector data types, usually by simply calling the associated assembly instruction.

For example, here is a cycle that adds together two arrays of 64-bit floating-point numbers using AVX intrinsics:

```c++
double a[100], b[100], c[100];

// iterate in blocks of 4,
// because that's how many doubles can fit into a 256-bit register
for (int i = 0; i < 100; i += 4) {
    // load two 256-bit segments into registers
    __m256d x = _mm256_loadu_pd(&a[i]);
    __m256d y = _mm256_loadu_pd(&b[i]);

    // add 4+4 64-bit numbers together
    __m256d z = _mm256_add_pd(x, y);

    // write the 256-bit result into memory, starting with c[i]
    _mm256_storeu_pd(&c[i], z);
}
```

The main challenge of using SIMD is getting the data into contiguous fixed-sized blocks suitable for loading into registers. In the code above, we may in general have a problem if the length of the array is not divisible by the block size. There are two common solutions to this:

1. We can "overshoot" by iterating over the last incomplete segment either way. To make sure we don't segfault by trying to read from or write to a memory region we don't own, we need to pad the arrays to the nearest block size (typically with some "neutral" element, e.g., zero).
2. Make one iteration less and write a little loop in the end that calculates the remainder normally (with scalar operations).

Humans prefer #1 because it is simpler and results in less code, and compilers prefer #2 because they don't really have another legal option.

### Instruction References

Most SIMD intrinsics follow a naming convention similar to `_mm<size>_<action>_<type>` and correspond to a single analogously named assembly instruction. They become relatively self-explanatory once you get used to the assembly naming conventions, although sometimes it does seem like their names were generated by cats walking on keyboards (explain this: [punpcklqdq](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=3037,3009,4870,4870,4872,4875,833,879,874,849,848,6715,4845,6046,3853,288,6570,6527,6527,90,7307,6385,5993,2692,6946,6949,5456,6938,5456,1021,3007,514,518,4875,7253,7183,3892,5135,5260,5259,6385,3915,4027,3873,7401&techs=AVX,AVX2&text=punpcklqdq)).

Here are a few more examples, just so that you get the gist of it:

- `_mm_add_epi16`: add two 128-bit vectors of 16-bit *extended packed integers*, or simply said, `short`s.
- `_mm256_acos_pd`: calculate elementwise $\arccos$ for 4 *packed doubles*.
- `_mm256_broadcast_sd`: broadcast (copy) a `double` from a memory location to all 4 elements of the result vector.
- `_mm256_ceil_pd`: round up each of 4 `double`s to the nearest integer.
- `_mm256_cmpeq_epi32`: compare 8+8 packed `int`s and return a mask that contains ones for equal element pairs.
- `_mm256_blendv_ps`: pick elements from one of two vectors according to a mask.

As you may have guessed, there is a combinatorially very large number of intrinsics, and in addition to that, some instructions also have immediate values — so their intrinsics require compile-time constant parameters: for example, the floating-point comparison instruction [has 32 different modifiers](https://stackoverflow.com/questions/16988199/how-to-choose-avx-compare-predicate-variants).

For some reason, there are some operations that are agnostic to the type of data stored in registers, but only take a specific vector type (usually 32-bit float) — you just have to convert to and from it to use that intrinsic. To simplify the examples in this chapter, we will mostly work with 32-bit integers (`epi32`) in 256-bit AVX2 registers.

A very helpful reference for x86 SIMD intrinsics is the [Intel Intrinsics Guide](https://software.intel.com/sites/landingpage/IntrinsicsGuide/), which has groupings by categories and extensions, descriptions, pseudocode, associated assembly instructions, and their latency and throughput on Intel microarchitectures. You may want to bookmark that page.

The Intel reference is useful when you know that a specific instruction exists and just want to look up its name or performance info. When you don't know whether it exists, this [cheat sheet](https://db.in.tum.de/~finis/x86%20intrinsics%20cheat%20sheet%20v1.0.pdf) may do a better job.

**Instruction selection.** Note that compilers do not necessarily pick the exact instruction that you specify. Similar to the scalar `c = a + b` we [discussed before](/hpc/analyzing-performance/assembly), there is a fused vector addition instruction too, so instead of using 2+1+1=4 instructions per loop cycle, compiler [rewrites the code above](https://godbolt.org/z/dMz8E5Ye8) with blocks of 3 instructions like this:

```nasm
vmovapd ymm1, YMMWORD PTR a[rax]
vaddpd  ymm0, ymm1, YMMWORD PTR b[rax]
vmovapd YMMWORD PTR c[rax], ymm0
```

Sometimes, although quite rarely, this compiler interference makes things worse, so it is always a good idea to [check the assembly](/hpc/compilation/stages) and take a closer look at the emitted vector instructions (they usually start with a "v").

Also, some of the intrinsics don't map to a single instruction but a short sequence of them, as a convenient shortcut: [broadcasts and extracts](../moving#register-aliasing) are a notable example.

<!--

For example, the group of `extract` intrinsics that are used to get individual elements out of vectors: e g., `_mm256_extract_epi32(x, 0)` returns the first element out of 8-integer vector. t is quite slow (~5 cycles) to move data between "normal" and SIMD registers in general.

-->

### GCC Vector Extensions

If you feel like the design of C intrinsics is terrible, you are not alone. I've spent hundreds of hours writing SIMD code and reading the Intel Intrinsics Guide, and I still can't remember whether I need to type `_mm256` or `__m256`.

Intrinsics are not only hard to use but also neither portable nor maintainable. In good software, you don't want to maintain different procedures for each CPU: you want to implement it just once, in an architecture-agnostic way.

One day, compiler engineers from the GNU Project thought the same way and developed a way to define your own vector types that feel more like arrays with some operators overloaded to match the relevant instructions.

In GCC, here is how you can define a vector of 8 integers packed into a 256-bit (32-byte) register:

```c++
typedef int v8si __attribute__ (( vector_size(32) ));
// type ^   ^ typename          size in bytes ^ 
```

Unfortunately, this is not a part of the C or C++ standard, so different compilers use different syntax for that.

There is somewhat of a naming convention, which is to include size and type of elements into the name of the type: in the example above, we defined a "vector of 8 signed integers." But you may choose any name you want, like `vec`, `reg` or whatever. The only thing you don't want to do is to name it `vector` because of how much confusion there would be because of `std::vector`.

The main advantage of using these types is that for many operations you can use normal C++ operators instead of looking up the relevant intrinsic.

```c++
v4si a = {1, 2, 3, 5};
v4si b = {8, 13, 21, 34};

v4si c = a + b;

for (int i = 0; i < 4; i++)
    printf("%d\n", c[i]);

c *= 2; // multiply by scalar

for (int i = 0; i < 4; i++)
    printf("%d\n", c[i]);
```

With vector types we can greatly simplify the "a + b" loop we implemented with intrinsics before:

```c++
typedef double v4d __attribute__ (( vector_size(32) ));
v4d a[100/4], b[100/4], c[100/4];

for (int i = 0; i < 100/4; i++)
    c[i] = a[i] + b[i];
```

As you can see, vector extensions are much cleaner compared to the nightmare we have with intrinsic functions. Their downside is that there are some things that we may want to do are just not expressible with native C++ constructs, so we will still need intrinsics for them. Luckily, this is not an exclusive choice, because vector types support zero-cost conversion to the `_mm` types and back:

```c++
v8f x;
int mask = _mm256_movemask_ps((__m256) x)
```

There are also many third-party libraries for different languages that provide a similar capability to write portable SIMD code and also implement some, and just in general are nicer to use than both intrinsics and built-in vector types. Notable examples for C++ are [Highway](https://github.com/google/highway), [Expressive Vector Engine](https://github.com/jfalcou/eve), [Vector Class Library](https://github.com/vectorclass/version2), and [xsimd](https://github.com/xtensor-stack/xsimd).

Using a well-established SIMD library is recommended as it greatly improves the developer experience. In this book, however, we will try to keep close to the hardware and mostly use intrinsics directly, occasionally switching to the vector extensions for simplicity when we can.
