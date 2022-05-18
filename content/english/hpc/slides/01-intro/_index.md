---
title: Why Go Beyond Big O?
outputs: [Reveal]
---

# Performance Engineering

Sergey Slotin

$x + y$

May 7, 2022

---

### About me

- Former [competitive programmer](https://codeforces.com/profile/sslotin)
- Created [Algorithmica.org](https://ru.algorithmica.org/cs) and "co-founded" [Tinkoff Generation](https://algocode.ru/)
- Wrote [Algorithms for Modern Hardware](https://en.algorithmica.org/hpc/), on which these lectures are based
- Twitter: [@sergey_slotin](https://twitter.com/sergey_slotin); Telegram: [@bydlokoder](https://t.me/bydlokoder); anywhere else: @sslotin

----

### About this mini-course

- Low-level algorithm optimization
- Two days, six lectures
- **Day 1:** CPU architecture & assembly, pipelining, SIMD programming
- **Day 2:** CPU caches & memory, binary search, tree data structures
- Prerequisites: CS 102, C/C++
- No assignments, but you are encouraged to reproduce case studies: https://github.com/sslotin/amh-code

---

## Lecture 0: Why Go Beyond Big O

*(AMH chapter 1)*

---

## The RAM Model of Computation

- There is a set of *elementary operations* (read, write, add, multiply, divide)
- Each operation is executed sequentially and has some constant *cost*
- Running time ≈ sum of all elementary operations weghted by their costs

----

![](https://en.algorithmica.org/hpc/complexity/img/cpu.png =400x)

- The “elementary operations” of a CPU are called *instructions*
- Their “costs” are called *latencies* (measured in cycles)
- Instructions modify the state of the CPU stored in a number of *registers*
- To convert to real time, sum up all latencies of executed instructions and divide by the *clock frequency* (the number of cycles a particular CPU does per second) <!-- .element: class="fragment" data-fragment-index="1" -->
- Clock speed is volatile, so counting cycles is more useful for analytical purposes <!-- .element: class="fragment" data-fragment-index="1" -->

----

![](https://external-preview.redd.it/6PIp0RLbdWFGFUOT6tFuufpMlplgWdnXWOmjuqkpMMU.jpg?auto=webp&s=9bed495f3dbb994d7cdda33cc114aba1cebd30e2 =400x)

http://ithare.com/infographics-operation-costs-in-cpu-clock-cycles/

----

### Asymptotic complexity

![](https://en.algorithmica.org/hpc/complexity/img/complexity.jpg =400x)

For sufficiently large $n$, we only care about asymptotic complexity: $O(n) = O(1000 \cdot n)$

$\implies$ The costs of basic ops don't matter since they don't affect complexity <!-- .element: class="fragment" data-fragment-index="1" -->

But can we handle "sufficiently large" $n$? <!-- .element: class="fragment" data-fragment-index="2" -->

---

When complexity theory was developed, computers were different

![](https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Eniac.jpg/640px-Eniac.jpg =500x)

Bulky, costly, and fundamentally slow (due to speed of light)

----

![](https://researchresearch-news-wordpress-media-live.s3.eu-west-1.amazonaws.com/2022/02/microchip_fingertip-738x443.jpg =500x)

Micro-scale circuits allow signals to propagate faster

----

<style>
.randomname{
    display: flex;
    flex: 1em 5em;
}
</style>

<div class="randomname">

<div style="flex: 1; margin-top: -30px">

![](https://en.algorithmica.org/hpc/complexity/img/lithography.png =450x)    

</div>

<div style="flex: 2">

Microchips are "printed" on a slice of silicon using a procees called [photolithography](https://en.wikipedia.org/wiki/Photolithography):

1. grow and slice a [very pure silicon crystal](https://en.wikipedia.org/wiki/Wafer_(electronics))
2. cover it with a layer of [photoresist](https://en.wikipedia.org/wiki/Photoresist)
3. hit it with photons in a set pattern
4. chemically [etch](https://en.wikipedia.org/wiki/Etching_(microfabrication)) the exposed parts
5. remove the remaining photoresist

(…plus another 40-50 steps over several months to complete the rest of the CPU)
    
</div>

</div>

----

The development of microchips and photolithography enabled:

- higher clock rates
- the ability to scale the production
- **much** lower material and power usage (= lower cost)

----

![](https://upload.wikimedia.org/wikipedia/commons/4/49/MOS_6502AD_4585_top.jpg =500x)

MOS Technology 6502 (1975), Atari 2600 (1977), Apple II (1977), Commodore 64 (1982)

----

Also a clear path to improvement: just make lenses stronger and chips smaller

**Moore’s law:** transistor count doubles every two years. <!-- .element: class="fragment" data-fragment-index="1" -->

----

**Dennard scaling:** reducing die dimensions by 30%

- doubles the transistor density ($0.7^2 \approx 0.5$)
- increases the clock speed by 40% ($\frac{1}{0.7} \approx 1.4$)
- leaves the overall *power density* the same
  (we have a mechanical limit on how much heat can be dissipated)

$\implies$ Each new "generation" should have roughly the same total cost, but 40% higher clock and twice as many transistors

(which can be used, e.g., to add new instructions or increase the word size) <!-- .element: class="fragment" data-fragment-index="1" -->

----

Around 2005, Dennard scaling stopped — due to *leakage* issues:

- transistors became very smal
- $\implies$ their magnetic fields started to interfere with the neighboring circuitry
- $\implies$ unnecessary heating and occasional bit flipping
- $\implies$ have to increase voltage to fix it
- $\implies$ have to reduce clock frequency to balance off power consumption

----

![](https://en.algorithmica.org/hpc/complexity/img/dennard.ppm =600x)

A limit on the clock speed

---

Clock rates have plateaued, but we still have more transistors to use:

- **Pipelining:** overlapping the execution of sequential instructions to keep different parts of the CPU busy
- **Out-of-order execution:** no waiting for the previous instructions to complete
- **Superscalar processing:** adding duplicates of execution units
- **Caching:** adding layers of faster memory on the chip to speed up RAM access
- **SIMD:** adding instructions that handle a block of 128, 256, or 512 bits of data
- **Parallel computing:** adding multiple identinal cores on a chip
- **Distributed computing:** multiple chips in a motherboard or multiple computers
- **FPGAs** and **ASICs:** using custom hardware to solve a specific problem

----

![](https://en.algorithmica.org/hpc/complexity/img/die-shot.jpg =500x)

For modern computers, the “let’s count all operations” approach for predicting algorithm performance is off by several orders of magnitude

---

### Matrix multiplication

```python
n = 1024

a = [[random.random()
      for row in range(n)]
      for col in range(n)]

b = [[random.random()
      for row in range(n)]
      for col in range(n)]

c = [[0
      for row in range(n)]
      for col in range(n)]

for i in range(n):
    for j in range(n):
        for k in range(n):
            c[i][j] += a[i][k] * b[k][j]
```

630 seconds or 10.5 minutes to multiply two $1024 \times 1024$ matrices in plain Python

~880 cycles per multiplication

----

```java
public class Matmul {
    static int n = 1024;
    static double[][] a = new double[n][n];
    static double[][] b = new double[n][n];
    static double[][] c = new double[n][n];

    public static void main(String[] args) {
        Random rand = new Random();

        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                a[i][j] = rand.nextDouble();
                b[i][j] = rand.nextDouble();
                c[i][j] = 0;
            }
        }

        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                for (int k = 0; k < n; k++)
                    c[i][j] += a[i][k] * b[k][j];
    }
}
```

Java needs 10 seconds, 63 times faster

~13 cycles per multiplication

----

```c
#define n 1024
double a[n][n], b[n][n], c[n][n];

int main() {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            a[i][j] = (double) rand() / RAND_MAX;
            b[i][j] = (double) rand() / RAND_MAX;
        }
    }

    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                c[i][j] += a[i][k] * b[k][j];
    
    return 0;
}
```

`GCC -O3` needs 9 seconds, but if we include `-march=native` and `-ffast-math`, the compiler vectorizes the code, and it drops down to 0.6s.

----

```python
import time
import numpy as np

n = 1024

a = np.random.rand(n, n)
b = np.random.rand(n, n)

start = time.time()

c = np.dot(a, b)

duration = time.time() - start
print(duration)
```

BLAS needs ~0.12 seconds
(~5x over auto-vectorized C and ~5250x over plain Python)
