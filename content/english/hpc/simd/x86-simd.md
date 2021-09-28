---
title: Intrinsics and Vector Extensions
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

## Vector Extensions

If you feel like the design of C++ intrinsics is terrible, you are not alone. I've spent dozens of hours on the intel intrinsics guide, and I still can't remember whether I need to type `_mm256` or `__m256`.

They are not only hard to use, but also neither portable nor maintainable. A good software is the one where we don't need to implement multiple procedure for each CPU, and just write it once, in architecture-agnostic way.

One day, compiler engineers from the GNU Project thought the same way and developed a special vector types that feel more like arrays with some operators overloaded to match to relevant instructions.

In GCC, here is how you can define vector of 8 integers packed into 256-bit (32-byte) register:

```c++
typedef int v8si __attribute__ (( vector_size(32) ));
// type ^   ^ typename          size in bytes ^ 
```

Unfortunately, this syntax is not universal, so different compilers may use different syntax.

There is somewhat of a naming convention, which is to include size and type of elements into the name of the type. In this case, we defined a "vector of 8 signed integers". But you may choose any name you want, like `vec`, `reg` or whatever. The only thing you don't want to do is to name it `vector` because of how much headache and confusion there will be because of `std::vector`.

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

Let's rewrite the same "a + b" loop using vector types:

```c++
typedef double v4d __attribute__ (( vector_size(32) ));
v4d a[100/4], b[100/4], c[100/4];

for (int i = 0; i < 100/4; i++)
    c[i] = a[i] + b[i];
```

Armed with a nicer syntax, let's consider a slightly more complex example: summing up an array. The naive approach is not so straightforward to vectorize, because the state of the loop (sum of the current prefix) depends on the previous iteration:

```c++
int sum_naive(int *a, int n) {
    int s = 0;
    for (int i = 0; i < n; i++)
        s += a[i];
    return s;
}
```

The way to overcome this is to split a single scalar accumulator (`s`) into 8 separate ones, where $s_i$ would contain the sum of $\\{ a_{8 \cdot j + i } \\}$, that is, every 8th element of the original array, shifted by $i$. If we store the 8 accumulators in a 256-bit vector, we can update them all at once by adding consecutive 8-elements segments of the array:

```c++
int sum_simd(v8si *a, int n) {
    //       ^ you can just cast a pointer normally, like with any other pointer type
    v8si s = {0};

    for (int i = 0; i < n / 8; i++)
        s += a[i];
    
    int res = 0;
    
    // sum 8 accumulators into one 
    for (int i = 0; i < 8; i++)
        res += s[i];

    // add the remainder of a
    for (int i = n / 8 * 8; i < n; i++)
        res += a[i];
        
    return res;
}
```

The part where we sum up 8 accumulators to get the total sum can be done a bit faster by what's called a "horizontal sum", which is the repeated use of [special instructions](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#techs=AVX,AVX2&text=_mm256_hadd_epi32&expand=2941) that add together pairs of adjacent elements:

```c++
int hsum(v8si s) {
    // TODO
    // https://stackoverflow.com/questions/42000693/why-my-avx2-horizontal-addition-function-is-not-faster-than-non-simd-addition
}
```

Although this is approximately how compilers vectorize array reductions, this is not the fastest way to do it. We will [come back](../../instruction-level-parallelism/throughput) to this problem in the next chapter.

Vector extensions are much clearer compared to the intrinsic nightmare, but some things that we may want to do are just not expressible with native C++ constructs, so we will still need intrinsics—which is not a exclusive choice, because vector types support conversion to "`_mm`" types and back. We will try, however, to avoid doing so as much as possible.

