---
title: Instruction-Level Parallelism
---

### Most of CPU isn't about computing

![](https://abload.de/img/5017e5_727ef30243c547j9kue.jpg =500x)

Hi-res shot of AMD "Zen" core die

----

![](https://thezeroalpha.github.io/sysarch-notes/Superscalar%20operation.resources/screenshot.png =600x)

It actually takes way more than one cycle to execute *anything*

----

## Pipelining

Modern CPUs attempt to keep every part of the processor busy with some instruction

![](https://simplecore-ger.intel.com/techdecoded/wp-content/uploads/sites/11/figure-2-3.png)

$\text{# of instructions} \to \infty,\; CPI \to 1$

----

![](https://media.ford.com/content/fordmedia/fna/us/en/features/game-changer--100th-anniversary-of-the-moving-assembly-line.img.png/1500004048707.jpg =600x)

Real-world analogue: Henry Ford's assembly line

----

## Superscalar Processors

![](https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Superscalarpipeline.svg/2880px-Superscalarpipeline.svg.png =500x)

CPI could be less than 1 if we have more than one of everything

----

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

---

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