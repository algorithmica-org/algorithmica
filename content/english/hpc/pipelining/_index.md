---
title: Instruction-Level Parallelism
weight: 3
---

When programmers hear the word *parallelism*, they mostly think about *multi-core parallelism*, the practice of explicitly splitting a computation into semi-independent *threads* that work together to solve a common problem.

This type of parallelism is mainly about reducing *latency* and achieving *scalability*, but not about improving *efficiency*. You can solve a problem ten times as big with a parallel algorithm, but it would take at least ten times as many computational resources. Although parallel hardware is becoming [ever more abundant](/hpc/complexity/hardware), and parallel algorithm design is becoming an increasingly more important area, for now, we will consider the use of more than one CPU core cheating.

But there are other types of parallelism, already existing inside a CPU core, that you can use *for free*.

<!--

This technique only applies 

Parallel hardware is now everywhere. When you opened this page in your browser, it was retrieved by a 50-core server CPU, then parsed by an 8-core desktop CPU, and then rendered by a 400-core GPU. Not all cores were involved with serving you this page at all times — they might have been doing something else.

Parallelism helps in reducing *latency*. It is important, but for now, our main concern is not *scalability*, but *efficiency* of algorithms.

Sharing computations is an art in itself, but for now, we want to learn how to use resources that we already have more efficiently.

While multi-core parallelism is "cheating", many form of parallelism exist  "for free".

Adapting algorithms for parallel hardware is important for achieving *scalability*. In the first part of this book, we will consider this technique "cheating". We only do optimizations that are truly free, and preferably don't take away resources from other processes that might be running concurrently.

-->

### Instruction Pipelining

To execute *any* instruction, processors need to do a lot of preparatory work first, which includes:

- **fetching** a chunk of machine code from memory,
- **decoding** it and splitting into instructions,
- **executing** these instructions, which may involve doing some **memory** operations, and
- **writing** the results back into registers.

This whole sequence of operations is *long*. It takes up to 15-20 CPU cycles even for something simple like `add`-ing two register-stored values together. To hide this latency, modern CPUs use *pipelining*: after an instruction passes through the first stage, they start processing the next one right away, without waiting for the previous one to fully complete.

![](img/pipeline.png)

Pipelining does not reduce *actual* latency but functionally makes it seem like if it was composed of only the execution and memory stage. You still need to pay these 15-20 cycles, but you only need to do it once after you've found the sequence of instructions you are going to execute.

Having this in mind, hardware manufacturers like to use *cycles per instruction* (CPI) instead of something like "average instruction latency" as the main performance indicator for CPU designs. It is a [pretty good metric](/hpc/profiling/benchmarking) for algorithm designs too, if we only consider *useful* instructions.

### Superscalar Processors

CPI of a perfectly pipelined processor should tend to one, but it can actually be even lower than one.

As there are many different instructions, It is very common for programs to have groups of logically independent operations that can be processed separately by different execution units. To improve their utilization, we can duplicate everything else the pipeline so that more than one instruction is processed in a time, and then, if possible, schedule the instructions on different parts of the ALU. Such architectures, capable of executing more than one, are called *superscalar*, and most modern CPUs are.

<!-- Pipeline of a superscalar CPU with the width of 2 img/superscalar.png -->

Interleaving the stages of execution is a general idea in digital electronics, and it is applied not only in the main CPU pipeline, but also on the level of separate instructions and [memory](/hpc/cpu-cache/mlp). Most execution units have their own little pipelines, and can take another instruction just one or two cycles after the previous one. If a certain instruction is frequently used, it makes sense to duplicate its execution unit also, and also place frequently jointly used instructions on the same execution unit: e. g. not using the same for arithmetic and memory operation.

### Microcode

While complex instruction sets had the benefit, with superscalar processors you want your instructions to be as tiny and atomic as possible. Such as fused add instruction. This also provides a simple way to "retire" old instructions that nobody is using and you don't want to support anymore: just replace them with a hundred or so microcoded instruction. They are not used anyway.

Instructions are microcoded.

uOps ("micro-ops", the first letter is meant to be greek letter mu as in us (microsecond), but nobody cares enough to type it).

Each architecture has its own set of "ports", each capable of executing its own set of instructions (uOps, to be more exact).

But still, when you use it, it appears and feels like a single instruction. How does CPU achieve that?

### Instruction Scheduling

This poses some additional challenges in coordinating how to execute instruction and in which order. This is why modern schedulers take more die space than the entirety of the integer ALU. They are insanely complex, but this mental model works good enough most of the time.

Modern processors don’t actually execute instructions one-by-one, but maintain a *pipeline* of pending instructions so that two independent operations can be executed concurrently without waiting for each other to finish.

Out-of-order execution. A buffer of pending instructions.

A bit more precisely, the CPU will look at the instruction stream up to some distance in the future. If there are branches, it will do branch prediction to produce a sequential stream of instructions. Then it will see which of the instructions are ready for execution. For example, if it sees a future instruction X that only uses registers A and B, and there are no instructions before it that touch those registers, and none of the instructions that are currently in the pipeline modify those registers, either, then it is safe to start to execute X as soon as there is an execution unit that is available.

All of this happens in the hardware, all the time, fully automatically. The only thing that the programmer needs to do is to make sure there are sufficiently many independent instructions always available for execution. The magic takes place inside the CPU. The compiler just produces two machine language instructions, without any special annotation that indicates whether or not these instructions can be executed in parallel. The CPU will then automatically figure out which of the instructions can be executed in parallel.

You can schedule independent instructions separately, but only up to some extent. This buffer is large, hundreds of operations. Still not enough for something extra long like main memory accesses.

### Instruction Timings

In this context, it makes sense to use two different "[costs](/hpc/complexity)" for instructions:

- *Latency*: how many cycles are needed to receive the results of an instruction.
- *Throughput*: how many instructions can be, on average, executed per cycle.

Because our minds are so used to the cost model where "more" means "worse", it makes sense to use the reciprocals of throughput. It can be less than zero — because of superscalar processors.

The latency and throughput numbers are architecture-specific. You can get this data from special documents called [instruction tables](https://www.agner.org/optimize/instruction_tables.pdf). Some sample values for my Zen 2 (all are specified for 32-bit integers, if there is any difference):

| Instruction | Latency | RThroughput |
|-------------|---------|:------------|
| `jmp`       | -       | 2           |
| `mov r, r`  | -       | 1/4         |
| `mov r, m`  | 4       | 1/2         |
| `mov m, r`  | 3       | 1           |
| `add`       | 1       | 1/3         |
| `cmp`       | 1       | 1/4         |
| `popcnt`    | 1       | 1/4         |
| `mul`       | 3       | 1           |
| `div`       | 13-28   | 13-28       |

Some caveats:

- Some instructions have a latency of 0. This means that these instruction are used to control the scheduler, and they don't reach the execution stage. This is by the virtue of renaming. But they still have non-zero latency because we first need to [process them](/hpc/architecture/layout). Decode width. You can't get throughput higher than that.
- Most instructions are pipelined. Throughput means that after exactly $n$ cycles it can take another one. [Integer division](/hpc/arithmetic/division) is an exception: it is either very poorly pipelined or not pipelined at all (like in this case).
- You could consider that the latency is zero or undefined. For memory operations, latency is usually specified for L1 cache. Latency can be dependent on data (again, division). Sometimes operations have many forms. For example, "mov" with memory operands does. Fused operations do memory accesses to.
- Some instruction tables also list execution ports (or sometimes "pipes"). This is mostly relevant for SIMD.

This is a bit of an advanced and not well understood topic. Documentation is very obscure. people have to reverse engineer it. There are reasons to believe that folks at Intel don't know that themselves. The most comprehensive one is probably, uops.info.

There are tools like llvm-mca, but they aren't perfect either.

### An Education Analogy

As a everyday metaphor, consider how a university works. It could have one student at a time and around 50 professors, which would take turns in tutoring, but this would be highly inefficient and result in one bachelor's degree every 4 year.

Maybe this is how the members of the British royal family study.

But for better of worse, the education is scaled.

Instead, universities do two smart things:

1. They teach to large groups of students at once instead of individuals, broadcasting the same thing (SIMD).
2. They might split work between different parallel groups (superscalar processing).
2. They overlap their classes so that each can all professors keep busy. This way you can increase throughput by 4x.

For the first trick, the CPU world analogue is SIMD, which we covered in the previous chapter. And for the second, it is the technique called pipelining, which we are going to discuss next.

Kind of match.

1. SIMD to process 16, 32, or 64 bytes of data at a time.
2. Superscalar processing to handle 2 to 4 SIMD blocks at a time
3. Pipelining (~15, roughly equal to the number of years between kindergarten and PhD)

In addition to that, other aspects are also true. Execution paths become more divergent. Some are stalled at various stages. Also some are interrupted. Some are speculated without knowing what happens.

There are many aspects, and in this chapter we are going to explore them

You might fail a course, but proceed somewhere else.

Similar to education, these also cause problems, and the first thing we will do in this chapter is learn how to avoid them.

Programming pipelined and superscalar processors presents its own challenges, which we are going to address in this chapter.
