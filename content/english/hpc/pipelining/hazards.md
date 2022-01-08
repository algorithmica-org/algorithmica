---
title: Pipeline Hazards
weight: 1
---

situations that prevent the next instruction in the instruction stream from executing during its designated clock cycles

Let's dive deeper into microarchitecture.

![](https://thezeroalpha.github.io/sysarch-notes/Superscalar%20operation.resources/screenshot.png =600x)

It actually takes way more than one cycle to execute *anything*

What exactly happens when the code is fed into compiler?

1. Some internal representation. LLVM
2. Optimization.
3. Assembly.
4. Machine code.

Just to be clear, here we are talking about "real" compiled languages, like C, C++, Go or Rust.

Java and Python doesn't count. Java is an interpreted language too from the standpoint that it needs and interpreter. It is just that it gets turned into internal representation beforehand.

## x86 Pipelining

Processors consist of multiple units.

Similar to Henry Ford's assembly line, modern CPUs attempt to keep every part of the processor busy with some instruction

![](https://simplecore-ger.intel.com/techdecoded/wp-content/uploads/sites/11/figure-2-3.png)

$\text{# of instructions} \to \infty,\; CPI \to 1$

1. Fetch
2. Decode: sets up necessary data
3. Execute: sends on a separate execution unit
4. Write: write data back to registers or set some flag

## Latency and Throughput

| Operation | Latency | $\frac{1}{throughput}$ |
| --------- | ------- |:------------ |
| MOV       | 1       | 1/3          |
| JMP       | 0       | 2            |
| ADD       | 1       | 1/3          |
| SUM       | 1       | 1/3          |
| CMP       | 1       | 1/3          |
| POPCNT    | 3       | 1            |
| MUL       | 3       | 1            |
| DIV       | 11-21   | 7-11         |

"Nehalem" (Intel i7) op tables
https://www.agner.org/optimize/instruction_tables.pdf

### Superscalar Processors

![](https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Superscalarpipeline.svg/2880px-Superscalarpipeline.svg.png =500x)

CPI could be less than 1 if we have more than one of everything

----



## Hazards

* Data hazard: waiting for an operand to be computed from a previous step
* Structural hazard: two instructions need the same part of CPU
* Control hazard: have to clear pipeline because of conditionals

![](https://simplecore-ger.intel.com/techdecoded/wp-content/uploads/sites/11/figure-6-3.png)

Hazards create *bubbles*, or pipeline stalls

(i/o operations are "fire and forget", so they don't block execution)
<!-- .element: class="fragment" data-fragment-index="1" -->

----

## Branch Misprediction

Guessing the "wrong" side of "if" is costly because it interupts the pipeline

```cpp
// (assume "-O0")
for (int i = 0; i < n; i++)
    a[i] = rand() % 256;

sort(a, a + n); // <- runs 6x (!!!) faster when sorted
int sum = 0;

for (int t = 0; t < 1000; t++) { // <- so that we are not bottlenecked by i/o (n < L1 cache size)
    for (int i = 0; i < n; i++)
        if (a[i] >= 128)
            sum += a[i];
```

Minified code sample from [the most upvoted Stackoverflow answer ever](https://stackoverflow.com/questions/11227809/why-is-processing-a-sorted-array-faster-than-processing-an-unsorted-array)

----

### Mitigation Strategies

* Hardware (stats-based) branch predictor is built-in in CPUs,
* $\implies$ Replacing high-entropy `if`'s with predictable ones help
* You can replace conditional assignments with arithmetic:
  `x = cond * a + (1 - cond) * b`
* This became a common pattern, so CPU manufacturers added `CMOV` op
  that does `x = (cond ? a : b)` in one cycle
* *^This masking trick will be used a lot for SIMD and CUDA later*
* C++20 has added `[[likely]]` and `[[unlikely]]` attributes to provide hints:

```cpp
int f(int i) {
    if (i < 0) [[unlikely]] {
        return 0;
    }
    return 1;
}
```