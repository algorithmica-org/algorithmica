---
title: High Performance Computing
menuTitle: HPC
weight: 5
authors:
- Sergey Slotin
created: "Feb 2021"
date: 2021-04-18
---

This is a work-in-progress Computer Science book titled "Supercomputing for Mere Mortals".

It is split in 3 parts:

1. [Performance Engineering](cpu), which is getting close to completion.
2. [Parallel Computing](parallel), which is still in the research stage.
3. [Distributed Computing](distributed), which doesn't even have a general curriculum yet.

Unlike a traditional book, this one will change over time, evolving in parallel with new improvements in hardware and software and my understanding of them.

All materials are hosted on GitHub, with code in a separate repository. This isn't a collaborative project, but any contributions and feedback are welcome.

### Disclaimer: Technology Choices

The examples in this book use C++, GCC, x86-64, CUDA and Spark, although the underlying principles we aim to convey are not specific to them.

To clear my conscience, I'm not happy with any of these choices: these technologies just happen to be the most widespread and stable at the moment, and thus more helpful for the reader. I would have respectively picked C / Rust, LLVM, arm, OpenCL and Dask; maybe there will be a 2nd edition in which some of the tech stack is changed.

## Preface

If you ever opened a Computer Science textbook, it probably introduced *computational complexity* somewhere in the very beginning.

Simply put, it is the total count of *elementary operations* (additions, multiplications, reads, writes…) that are executed during a computation, possibly weighted by their *costs*. When we say "matrix multiplication requires $2nmk$ floating-point operations", we mean exactly that.

We can roughly predict the execution time using this count, because this cost model approximates how real computers work. The elementary operations of a CPU are called *instructions*, which have different *latencies*. These latencies depend on *clock frequency*, which is a volatile and often unknown variable, but when expressed in terms of *clock cycles*, they are somewhat consistent accross different CPUs.

Similarly to how the sum of these latencies can be used as a clock-independent proxy for the execution time, computational complexity can be used to quantify the *intrinsic time requirements* of an algorithm, without relying on the choice of a specific computer.

A few pages later, *asymptotic complexity* is introduced. It makes things simpler by replacing the total number of operations with an estimate that, on sufficiently large inputs, is only off by no more than a constant factor. This way, verbose "$(2 \cdot n^3 + 5 \cdot n^2 + 12)$ operations" turns into plain "$\Theta(n^3)$".

Although the elementary operations may have had different associated "costs" initially, at this point they are just hidden in the "Big O" along with all the other intricacies of the hardware.

The reason we use asymptotic complexity is because it provides simplicity while still being just precise enough to yield useful results about relative algorithm performance on large datasets. Under the promise that computers will eventually become fast enough to handle any "sufficiently large" input in a reasonable amount of time, asymptotically faster algorithms will always be faster in real time too, regardless of the hidden constant.

But this promise turned out to be not true, at least not in terms of clock speeds and instruction latencies.

### Processor Design

It may come as a surprise, but the primary metric for modern CPUs is not the clock frequency, but rather "useful operations per joule", or, more practically put, "useful operations per dollar".

Thermodynamically, a computer is just a very efficient device for converting electrical power into heat. Since this heat eventually needs to be removed — and it's not straightforward to do when you are working with a millimeter-scale crystal — there are physical limits of how much power you can consume and then dissipate. And even when under that limit, power efficiency is still important due to the cost of electricity: for a data center, the amortized cost of powering and cooling a busy server for 2-3 years is comparable to its the price of the server itself.

Historically, the three main variables guiding microchip designs are power, performance and area (PPA), commonly defined in watts, hertz and nanometers. Until ~2005, cost, which was mainly a function of area, and performance, used to be the most important criteria. But as battery-driven mobile devices started replacing PCs, power quickly and firmly moved up on top of the list, followed by cost and performance.

Modern microchips are "[printed](https://en.wikipedia.org/wiki/Photolithography)" on a slice of crystalline silicon, and one relatively easy way to increase all three main aspects of a CPU design is to simply scale the device. A smaller, but nearly identical circuit would require proportionally less materials (A), and smaller transistors would take less time to switch, allowing reducing the voltage (first P) and increasing the clock rate (second P). A more detailed observation, known as the *Dennard scaling*, states that reducting transistor dimensions by 30% doubles the transistor density ($0.7^2 \approx 0.5$), increases the clock speed by 40% ($\frac{1}{0.7} \approx 1.4$), and leaves the power consumption the same — with the same total area and twice the number of transistors, which can also be used to .

Dennard observes that transistor dimensions could be scaled by -30% (0.7x) every technology generation, thus reducing their area by 50%. This would reduce circuit delays by 30% (0.7x) and therefore increase operating frequency by about 40% (1.4x). Finally, to keep the electric field constant, voltage is reduced by 30%, reducing energy by 65% and power (at 1.4x frequency) by 50%.[note 1] Therefore, in every technology generation, if the transistor density doubles, the circuit becomes 40% faster, and power consumption (with twice the number of transistors) stays the same.[4]

In practical, we don't want to change

As power didn't matter that much in the early days of computing, frequency was increased, and the power use stayed in proportion with the area. This observation is known as Dennard scaling.

Throughout most of the computing history, optical shrinking was the main driving force behind performance improvements. Gordon Moore, former CEO of Intel, made a prediction in 1975 that transistor counts in microprocessors will double every two years. His prediction held to this day, and since become known as a "law". Because of the PPA trade-offs you can make during the design, the size of the fabrication process itself, such as "180nm" or "65nm", became the trademark for CPU efficiency.

![](img/dennard.ppm)

Both Dennard scaling and Moore's law are just observations made by engineers and tech executives, and not actual laws of physics. Dennard scaling faced the limitations of physics around 2005–2007, when it became too difficult to remove heat fast enough at such small sizes. Clock rates could no longer be increased by scaling, and the miniaturization trend started to slow down.

To avoid upsetting and confusing consumers with this new reality, chip makers agreed to stop delineating their chips by the size of their components. A special comittee had a meeting every two years where they took the previous node name, divided by the square root of two, rounded to the nearest integer, declared that result to be the new node name, and then drank lots of wine. Chip makers now group components into generations by the time that they where made, and so "nm" doesn't mean nanometer anymore.

### Modern Hardware

But Moore's law is not dead yet. Clock rates plateaued, but the progress didn't stop. Instead of chasing faster cycles, CPU designs started to focus on getting more useful things done in a single cycle. Instead of getting smaller, transistors have been changing shape.

This resulted in increasingly complex architectures capable of doing dozens, hundreds or thousands of different things every cycle. And from programmer's perspective, "let's count all operations" approach isn't just slightly wrong, but is off by several orders of magnitude.

And this is what this book is about: creating algorithms for modern hardware. Theoretical Computer Science is now what's called a dead field. Really exciting things stopped happening in the 70s; everything past that are just attempts to replace logarithms in the asymptotic with something slightly less than logarithms.

In this book, you will probably not learn a single asymptotically faster algorithm, but you master much more practical ways to speed up a program than by going from $O(n \log n)$ to $O(n \log \log n)$.
