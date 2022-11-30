---
title: Instruction Scheduling
weight: 4
draft: true
---

Let's dive a bit deeper.

### Superscalar Processors

CPI of a perfectly pipelined processor should tend to one, but it can actually be even lower than one.

As there are many different instructions, It is very common for programs to have groups of logically independent operations that can be processed separately by different execution units. To improve their utilization, we can duplicate everything else the pipeline so that more than one instruction is processed in a time, and then, if possible, schedule the instructions on different parts of the ALU. Such architectures, capable of executing more than one, are called *superscalar*, and most modern CPUs are.

<!-- Pipeline of a superscalar CPU with the width of 2 img/superscalar.png -->

Interleaving the stages of execution is a general idea in digital electronics, and it is applied not only in the main CPU pipeline, but also on the level of separate instructions and [memory](/hpc/cpu-cache/mlp). Most execution units have their own little pipelines, and can take another instruction just one or two cycles after the previous one. If a certain instruction is frequently used, it makes sense to duplicate its execution unit also, and also place frequently jointly used instructions on the same execution unit: e.g., not using the same for arithmetic and memory operation.

### Microcode

While complex instruction sets had the benefit, with superscalar processors you want your instructions to be as tiny and atomic as possible. Such as fused add instruction. This also provides a simple way to "retire" old instructions that nobody is using and you don't want to support anymore: just replace them with a hundred or so microcoded instruction. They are not used anyway.

Instructions are microcoded.

uOps ("micro-ops," the first letter is meant to be greek letter mu as in us (microsecond), but nobody cares enough to type it).

Each architecture has its own set of "ports," each capable of executing its own set of instructions (uOps, to be more exact).

But still, when you use it, it appears and feels like a single instruction. How does CPU achieve that?

### Instruction Scheduling

This poses some additional challenges in coordinating how to execute instruction and in which order. This is why modern schedulers take more die space than the entirety of the integer ALU. They are insanely complex, but this mental model works good enough most of the time.

Modern processors don’t actually execute instructions one-by-one, but maintain a *pipeline* of pending instructions so that two independent operations can be executed concurrently without waiting for each other to finish.

Out-of-order execution. A buffer of pending instructions.

A bit more precisely, the CPU will look at the instruction stream up to some distance in the future. If there are branches, it will do branch prediction to produce a sequential stream of instructions. Then it will see which of the instructions are ready for execution. For example, if it sees a future instruction X that only uses registers A and B, and there are no instructions before it that touch those registers, and none of the instructions that are currently in the pipeline modify those registers, either, then it is safe to start to execute X as soon as there is an execution unit that is available.

All of this happens in the hardware, all the time, fully automatically. The only thing that the programmer needs to do is to make sure there are sufficiently many independent instructions always available for execution. The magic takes place inside the CPU. The compiler just produces two machine language instructions, without any special annotation that indicates whether or not these instructions can be executed in parallel. The CPU will then automatically figure out which of the instructions can be executed in parallel.

You can schedule independent instructions separately, but only up to some extent. This buffer is large, hundreds of operations. Still not enough for something extra long like main memory accesses.
