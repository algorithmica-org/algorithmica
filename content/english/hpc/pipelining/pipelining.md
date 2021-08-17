---
title: Pipelining
weight: 1
---

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

