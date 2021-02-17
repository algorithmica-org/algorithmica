---
title: Performance Engineering
weight: 1
---

How much does an operation "cost"? If you ever opened a Computer Science textbook in your life, it probably said something along these lines in the very beginning:

* Basic logical or arithmetic operations (e. g. `+`, `*`, `=`, `if`) are considered to take one time step.
* All memory access takes exactly one time step.
* Every operation is done sequentially.

This is called the "RAM model of computation"; it *encapsulates* of the core functionality of computers, but does not mimic them completely. The reason we use it is because it provides simplicity at a cost of absolute precision, resulting in a very useful practical tool.

In theoretical analysis, we don't even care what the "unit time" is: all that matters is the *asymptotic complexity*, that is, how our running time scales with input size. It may be on the order of nanoseconds (modern CPUs) or on the order of full seconds (the early Alan Turing computers, or the ones you can build in [Minecraft](https://www.youtube.com/watch?v=SbO0tqH8f5I)). 

To improve on an algorithm that is already complexity optimal, we need more precise tools and a stronger model. The first step to do it is to acknowledge that not all operations are equal.

## How CPUs Work

Processors have a concept of a *clock rate*, which refers to the frequency at which an electronic oscillator sends pulses through the curcuit, which change its state. Every *cycle*, something happens.

The clock rate is a variable. It may be adjusted during execution. For example, it frequently changes on mobile CPUs to consume lower energy most of the time and "burst" for a short period when it needs to do something compute-intensive.

Not all operations take unit time to complete. You can use special op tables to look it up. For example, on Intel i7
https://www.agner.org/optimize/instruction_tables.pdf

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

This model still hides a lot of complexity, but it will do for now.

Interestingly, some operations take less than one "amortized" cycle, but more on that [later](pipelining).

## How Memory Works

Here is a table [originally composed](https://gist.github.com/jboner/2841832) by Jeff Dean, mainly concerning I/O operations:

```
Latency Comparison Numbers (~2012)
----------------------------------
L1 cache reference                           0.5 ns
Branch mispredict                            5   ns
L2 cache reference                           7   ns                      14x L1 cache
Mutex lock/unlock                           25   ns
Main memory reference                      100   ns                      20x L2 cache, 200x L1 cache
Compress 1K bytes with Zippy             3,000   ns        3 us
Send 1K bytes over 1 Gbps network       10,000   ns       10 us
Read 4K randomly from SSD*             150,000   ns      150 us          ~1GB/sec SSD
Read 1 MB sequentially from memory     250,000   ns      250 us
Round trip within same datacenter      500,000   ns      500 us
Read 1 MB sequentially from SSD*     1,000,000   ns    1,000 us    1 ms  ~1GB/sec SSD, 4X memory
Disk seek                           10,000,000   ns   10,000 us   10 ms  20x datacenter roundtrip
Read 1 MB sequentially from disk    20,000,000   ns   20,000 us   20 ms  80x memory, 20X SSD
Send packet CA->Netherlands->CA    150,000,000   ns  150,000 us  150 ms

Notes
-----
1 ns = 10^-9 seconds
1 us = 10^-6 seconds = 1,000 ns
1 ms = 10^-3 seconds = 1,000 us = 1,000,000 ns
```

As you see, I/O are much more drastic. Accessing a variable can take less than nanosecond to $10^7$ ns.

This is why we will cover [memory](memory-model) first.
