---
title: Hazards
weight: 2
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