---
title: SIMD Instructions
draft: true
---


## Recall: Superscalar Processors

* Any instruction execution takes multiple steps
* To hide latency, everything is pipelined
* You can get CPI < 1 if you have more than one of each execution unit
* Performance engineering is basically about avoiding pipeline stalls

![](https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Superscalarpipeline.svg/2880px-Superscalarpipeline.svg.png =450x)

---

## Single Instruction, Multple Data

![](https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/SIMD.svg/1200px-SIMD.svg.png =450x)

Instructions that perform the same operation on multiple data points
(blocks of 128, 256 or 512 bits, also called *vectors*)

----

![](https://i0.wp.com/www.urtech.ca/wp-content/uploads/2017/11/Intel-mmx-sse-sse2-avx-AVX-512.png =500x)

Backwards-compatible up until AVX-512

(x86 specific; ARM and others have similar instruction sets)

----

You can check compatibility during runtime:

```cpp
cout << __builtin_cpu_supports("sse") << endl;
cout << __builtin_cpu_supports("sse2") << endl;
cout << __builtin_cpu_supports("avx") << endl;
cout << __builtin_cpu_supports("avx2") << endl;
cout << __builtin_cpu_supports("avx512f") << endl;
```

...or call `cat /proc/cpuinfo` and see CPU flags along with other info

---

## How to Use SIMD

Converting a program from scalar to vector one is called *vectorization*,
which can be achieved using a combination of:

* x86 assembly
* **C/C++ intrinsics**
* Vector types
* SIMD libraries
* **Auto-vectorization**

Later are simpler, former are more flexible

----

### Intel Intrinsics Guide

![](https://i.imgur.com/ZIzDidV.png =600x)

Because nobody likes to write assembly

https://software.intel.com/sites/landingpage/IntrinsicsGuide/

----

All C++ intrinsics can be included with `x86intrin.h`

```cpp
#pragma GCC target("avx2")
#pragma GCC optimize("O3")

#include <x86intrin.h>
#include <bits/stdc++.h>

using namespace std;
```

You can also drop pragmas and compile with `-O3 -march=native` instead

---

## The A+B Problem

```cpp
const int n = 1e5;
int a[n], b[n], c[n];

for (int t = 0; t < 100000; t++)
    for (int i = 0; i < n; i++)
        c[i] = a[i] + b[i];
```

Twice as fast (!) if you compile with AVX instruction set
(i. e. add `#pragma GCC target("avx2")` or `-march=native`)

----

## What Actually Happens

```cpp
double a[100], b[100], c[100];

for (int i = 0; i < 100; i += 4) {
    // load two 256-bit arrays into their respective registers
    __m256d x = _mm256_loadu_pd(&a[i]);
    __m256d y = _mm256_loadu_pd(&b[i]);
    // - 256 is the block size
    // - d stands for "double"
    // - pd stands for "packed double"

    // perform addition
    __m256d z = _mm256_add_pd(x, y);
    // write the result back into memory
    _mm256_storeu_pd(&c[i], z);
}

```

(I didn't come up with the op naming, don't blame me)

----

### More examples

* `_mm_add_epi16`: adds two 16-bit extended packed integers (128/16=8 short ints)
* `_mm256_acos_pd`: computes acos of 256/64=4 doubles
* `_mm256_broadcast_sd`: creates 4 copies of a number in a "normal" register
* `_mm256_ceil_pd`: rounds double up to nearest int
* `_mm256_cmpeq_epi32`: compares 8+8 packed ints and returns a (vector) mask that contains ones for elements that are equal
* `_mm256_blendv_ps`: blends elements from either one vector or another according to a mask (vectorized cmov, could be used to replace `if`)

----

### Vector Types

For some reason, C++ intrinsics have explicit typing, for example on AVX:
* `__m256` means float and only instructions ending with "ps" work
* `__m256d` means double and only instructions ending with "pd" work
* `__m256i` means different integers and only instructions ending with "epi/epu" wor

You can freely convert between them with C-style casting

----

Also, compiles have their own vector types:

```cpp
typedef float float8_t __attribute__ (( vector_size (8 * sizeof(float)) ));
float8_t v;
float first_element = v[0]; // you can index them as arrays
float8_t v_squared = v * v; // you can use a subset of normal C operations
float8_t v_doubled = _mm256_movemask_ps(v); // all C++ instrinsics work too
```

Note that this is a GCC feature; it will probably be standartized in C++ someday

https://gcc.gnu.org/onlinedocs/gcc-4.7.2/gcc/Vector-Extensions.html

---

## Data Alignment

The main disadvantage of SIMD is that you need to get data in vectors first

(and sometimes preprocessing is not worth the trouble)
<!-- .element: class="fragment" data-fragment-index="1" -->

----

![](https://i.imgur.com/TBRhLew.png =600x)

----

![](https://i.imgur.com/WNH9eCc.png =600x)

----

![](https://i.imgur.com/SsDwG6D.png =600x)

----

For arrays, you have two options:

1. Pad them with neutal elements (e. g. zeros)
2. Break loop on last block and proceed normally

Humans prefer #1, compilers prefer #2
<!-- .element: class="fragment" data-fragment-index="1" -->

---

## Reductions

* Calculating A+B is easy, because there are no data dependencies
* Calculating array sum is different: you need an accumulator from previous step
* But we can calculate $B$ partial sums $\{i+kB\}$ for each $i<B$ and sum them up<!-- .element: class="fragment" data-fragment-index="1" -->

![](https://lh3.googleusercontent.com/proxy/ovyDHaTtBkntJLFOok2m17fYS0ROX0BBy-x4jG1CsYKInNRZvDMQyG-j-DOpRHR6jhYVvX2mWBLZHi2SoDwWLJ4LhofzScPtkFxko6tlYWcFyBttn7gIy0BiWWlvkIcl6BZbRBjCR5_wdniz6sIKTr1rpN7M_whxvd0IrUGpXGwI7PwKxwLslF_h9Zv8gbstlV--dyc)
<!-- .element: class="fragment" data-fragment-index="1" -->

This trick works with any other commutative operator
<!-- .element: class="fragment" data-fragment-index="1" -->

----

Explicitly using C++ intrinsics:

```cpp
int sum(int a[], int n) {
    int res = 0;

    // we will store 8 partial sums here
    __m256i x = _mm256_setzero_si256();
    for (int i = 0; i + 8 < n; i += 8) {
        __m256i y = _mm256_loadu_si256((__m256i*) &a[i]);
        // add all 8 new numbers at once to their partial sums
        x = _mm256_add_epi32(x, y);
    }

    // sum 8 elements in our vector ("horizontal sum")
    int *b = (int*) &x;
    for (int i = 0; i < 8; i++)
        res += b[i];

    // add what's left of the array in case n % 8 != 0
    for (int i = (n / 8) * 8; i < n; i++)
        res += a[i];

    return res;
}
```

(Don't implement it yourself, compilers are smart enough to vectorize)

----

![](https://www.codeproject.com/KB/cpp/874396/Fig1.jpg)

Horizontal addition could be implemented a bit faster

---

## Memory Alignment

There are two ways to read / write a SIMD block from memory:

* `load` / `store` that segfault when the block doesn't fit a single cache line
* `loadu` / `storeu` that always work but are slower ("u" stands for unaligned)

When you can enforce aligned reads, always use the first one

----

Assuming that both arrays are initially aligned:

```cpp
void aplusb_unaligned() {
    for (int i = 3; i + 7 < n; i += 8) {
        __m256i x = _mm256_loadu_si256((__m256i*) &a[i]);
        __m256i y = _mm256_loadu_si256((__m256i*) &b[i]);
        __m256i z = _mm256_add_epi32(x, y);
        _mm256_storeu_si256((__m256i*) &c[i], z);
    }
}
```

...will be 30% slower than this:

```cpp
void aplusb_aligned() {
    for (int i = 0; i < n; i += 8) {
        __m256i x = _mm256_load_si256((__m256i*) &a[i]);
        __m256i y = _mm256_load_si256((__m256i*) &b[i]);
        __m256i z = _mm256_add_epi32(x, y);
        _mm256_store_si256((__m256i*) &c[i], z);
    }
}
```

In unaligned version, half of reads will be the "bad" ones requesting two cache lines

----

So always ask compiler to align memory for you:

```cpp
alignas(32) float a[n];

for (int i = 0; i < n; i += 8) {
    __m256 x = _mm256_load_ps(&a[i]);
    // ...
}
```

(This is also why compilers can't always auto-vectorize efficiently)
<!-- .element: class="fragment" data-fragment-index="1" -->

---

## Loop Unrolling

Simple loops often have some overhead from iterating:

```cpp
for (int i = 1; i < n; i++)
    a[i] = (i % b[i]);
```

It is often benefitial to "unroll" them like this:

```cpp
int i;
for (i = 1; i < n - 3; i += 4) {
    a[i] = (i % b[i]);
    a[i + 1] = ((i + 1) % b[i + 1]);
    a[i + 2] = ((i + 2) % b[i + 2]);
    a[i + 3] = ((i + 3) % b[i + 3]);
}

for (; i < n; i++)
    a[i] = (i % b[i]);
```

There are trade-offs to it, and compilers are sometimes wrong
Use `#pragma unroll` and `-unroll-loops` to hint compiler what to do

---

## More on Pipelining

![](https://uops.info/pipeline.png =300x)

https://uops.info

----

For example, in Sandy Bridge family there are 6 execution ports:
* Ports 0, 1, 5 are for arithmetic and logic operations (ALU)
* Ports 2, 3 are for memory reads
* Port 4 is for memory write

You can lookup them up in instruction tables
and see figure out which one is the bottleneck

---

## SIMD + ILP

* As all instructions, SIMD operations can be pipelined too
* To leverage it, we need to create opportunities for instruction-level parallelism
* A+B is fine, but array sum still has dependency on the previous vector <!-- .element: class="fragment" data-fragment-index="1" -->
* Apply the same trick: calculate partial sums, but using multiple registers <!-- .element: class="fragment" data-fragment-index="2" -->

----

For example, instead of this:

```cpp
s += a0;
s += a1;
s += a2;
s += a3;
...
```

...we split it between accumulators and utilize ILP:

```cpp
s0 += a0;
s1 += a1;
s0 += a2;
s1 += a3;
...
s = s0 + s1;
```

---

## Practical Tips

* Compile to assembly: `g++ -S ...` (or go to godbolt.org)
* See which loops get autovectorized: `g++ -fopt-info-vec-optimized ...`
* Typedefs can be handy: `typedef __m256i reg`
* You can use bitsets to "print" a SIMD register:

```cpp
template<typename T>
void print(T var) {
    unsigned *val = (unsigned*) &var;
    for (int i = 0; i < 4; i++)
        cout << bitset<32>(val[i]) << " ";
    cout << endl;
}