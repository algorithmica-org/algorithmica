---
title: Intrinsics
weight: 1
---

The lowest level possible is to use assembly instructions directly, but, as we promised in [chapter 1](../../assembly), we are not going to do that. Instead, we are going to use *intrinsic* functions that map to these instructions that are available in all modern C++ compilers.

## Setup

To use them, we need to do a little work.

First, we need to determine which extensions are supported by the hardware. On Linux, you can call `cat /proc/cpuinfo`, and on other platforms you'd better go to [WikiChip](https://en.wikichip.org/wiki/WikiChip) and look it up there using the name of the CPU. In either case, there should be a `flags` section that lists all the available extensions.

There are also built-in instructions to get this information in runtime, which are primarily used to avoid distributing a separate binary for each microarchitecture. Here is an example:

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

Second, we need to include a header file that contains the set of intrinsics we need. Similar to `<bits/stdc++.h>` in GCC, there is `<x86intrin.h>` header that contains all of them.

And last, we need to tell the compiler that the target CPU actually supports these extensions. This can be done either with `#pragma GCC target ...` as before, or with `-march=...` flag in the compiler options. If you are running the code on the same machine, you can set `-march=native` to auto-detect the microarchitecture.

## SIMD Registers

The most notable distinction between SIMD extensions is the support for wider registers:

- SSE added 16 128-bit registers called `xmm0` through `xmm15`.
- AVX added 16 256-bit registers called `ymm0` through `ymm15`.
- AVX512 added 16 512-bit registers called `zmm0` through `zmm15`.

As you can guess from the naming, and also from the fact that 512 bits already occupy a full cache line, x86 designers are not planning on adding wider registers anytime soon.

C/C++ compilers implement special *vector types* that refer to data stored in these registers:

- 128-bit `__m128`, `__m128d` and `__m128i` types for single-precision floating-point, double-precision floating-point and various integer data.
- 256-bit `__m256`, `__m256d`, `__m256i`.
- 512-bit `__m256`, `__m256d`, `__m256i`.

AVX512 also has 8 so-called *mask registers* `k0` through `k7`, which are used for blending data. We are not going to cover them and mostly use AVX2.

Registers themselves can hold data of any time, this is just needed for type checking. Headache as sometimes you have to cast them to another type (which is just happening compile-time anyway).

## SIMD Instructions

Intrinsics are C-style functions that do something with data of these types, usually by just calling the associated assembly instruction. Most of them follow a naming convention similar to this: `_mm<size>_<action>_<type>`, and are relatively self-explanatory once you get used to assembly naming conventions.

As you may have guessed, there is a combinatorially very large number of intrinsics. A very helpful reference for x86 intrinsics is the [Intel Intrinsics Guide](https://software.intel.com/sites/landingpage/IntrinsicsGuide/), which contains groupings by categories and extensions, descriptions, pseudocode, associated assembly intructions and their latency information on Intel microarchitectures. You may want to bookmark that page.

Here is a cycle that adds two arrays of 64-bit floating-point numbers using AVX intrinsics:

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

In general, we may have a problem here if the length of the array is not divisible by block size. There are two common fixes to this:

1. We can "overshoot" by iterating over the last incomplete segment anyway. To make sure sure we don't segfault by trying to write to a memory we don't own, we need to pad the arrays to the nearest block size (sometimes with some "neutral" element, e. g. zero).

2. Make one iteration less and write a little loop in the end that calculates the remainder normally (with scalar operations).

Humans prefer #1, because it is simpler and results in less code. Compilers prefer #2, because they don't really have another legal option.

---

Note that compiler does not necessarily pick the exact instructions that you specify. Similarly to the scalar `c = a + b` we studied before, there is a fused vector addition operation too, and instead of using 2+1+1=4 instructions per loop cycle, compiler rewrites it with blocks of 3 instructions like this:

```asm
vmovapd a(%rax), %ymm1
vaddpd  b(%rax), %ymm1, %ymm0
vmovapd %ymm0, c(%rax)
```

Also, some of these intrinsics are not direct instructions, but short sequences of instructions. Example of such is the `extract` group of instructions, which are used to get individual elements out of vectors (e. g. `_mm256_extract_epi32(x, 0)` returns the first element out of 8-integer vector).

Here are a few more examples just so that you get a gist of it:

- `_mm_add_epi16` — adds to 128-bit vectors of 16-bit *extended packed integers*, or simply said, `short`
- `_mm256_acos_pd` — calculates elementvise arccos for 4 *packed doubles*
- `_mm256_broadcast_sd` — broadcasts (copies) a `double` from a memory location to all 4 elements of result vector
- `_mm256_ceil_pd` — round up each of 4 `double`s to its nearest integer
- `_mm256_cmpeq_epi32` — compares 8+8 packed `int`s and returns a (vector) mask that contains ones for elements that are equal
- `_mm256_blendv_ps` — takes elements from either one vector or another according to a mask

The Intel reference is useful when you know that a specific instruction exists and just want to look up its name. If you looking for the right one, this [cheat sheet](https://db.in.tum.de/~finis/x86%20intrinsics%20cheat%20sheet%20v1.0.pdf) may do a better job.
