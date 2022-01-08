---
title: Parallel Computing
weight: 100
part: Parallel Computing
draft: true
---

Classic computer science algorithms aim to minimize *work*: the total sum of operations needed.

But how many arithmetic operations a computer performed to do a task is not something that people really care about. Moreover, as we previously saw, due to the complex nature of computer hardware, less work doesn't necessarily mean less running time or less resources used.

What we really care about is the­ running time and, occasianally, the cost of computation (expressed in CPU-seconds, watts, or straightly dollars).

## Moore's Law

*Moore's law* is the observation (made by [Gordon Moore](https://en.wikipedia.org/wiki/Gordon_Moore), the co-founder and former CEO of Intel) that the number of transistors in a microprocessor doubles about every two years. From practical perspective, this roughly means that the performance doubles as well.

![](img/moores-law.jpg)

Throughout most of computing history, the main thing manufacturers did to improve performance was simply increasing clock frequency. This was possible by the virtue of more precise technology allowing to smaller and smaller chips. However, around mid-2000s they ran into the fundamental problem of removing extra heat from the die. Running CPUs at higher frequencies is not only energy-inefficient, but at some point just physically impossible.

So, in the last 20 years there has been a shift in direction. Instead of trying to execute more cycles per second, let the processor do more usefull work per cycle. We have already seen applications of this in practice: pipelining allows some interlapping, and SIMD instructions allow processing data in small batches.

But a much more scalable solution is to put more independent cores on a die that can do independent work and communicate intermediate results to syncronize.

## Multithreading Hardware

Hyperthreading

Multiple CPU sockets per motherboard

You can get 400 cores at google

SIMD

GPUs
