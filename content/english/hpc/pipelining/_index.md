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

Having this in mind, hardware manufacturers prefer to use *cycles per instruction* (CPI) instead of something like "average instruction latency" as the main performance indicator for CPU designs. It is a [pretty good metric](/hpc/profiling/benchmarking) for algorithm designs too, if we only consider *useful* instructions.

CPI of a perfectly pipelined processor should tend to one, but it can actually be even lower if we make each stage of the pipeline "wider" by duplicating it, so that more than one instruction can be processed at a time. Because the cache and most of the ALU can be shared, this ends up being cheaper than adding a fully separate core. Such architectures, capable of executing more than one instruction per cycle, are called *superscalar*, and most modern CPUs are.

You can only take advantage of superscalar processing if the stream of instructions contains groups of logically independent operations that can be processed separately. The instructions don't always arrive in the most convenient order, so, when possible, modern CPUs can execute them *out-of-order* to improve overall utilization and minimize pipeline stalls. How this magic works is a topic for [a more advanced discussion](scheduling), but for now, you can assume that the CPU maintains a buffer of pending instructions up to some distance in the future, and executes them as soon as the values of its operands are computed and there is an execution unit available.

<!-- This poses some additional challenges in coordinating how to execute the instructions — and also in which order. -->

### Instruction Timings

Interleaving the stages of execution is a general idea in digital electronics, and it is applied not only in the main CPU pipeline, but also on the level of separate instructions and [memory](/hpc/cpu-cache/mlp). Most execution units have their own little pipelines and can take another instruction just one or two cycles after the previous one.

In this context, it makes sense to use two different "[costs](/hpc/complexity)" for instructions:

- *Latency*: how many cycles are needed to receive the results of an instruction.
- *Throughput*: how many instructions can be, on average, executed per cycle.

<!-- alternative throughput definitions, maybe in scheduling? -->

You can get latency and throughput numbers for a specific architecture from special documents called [instruction tables](https://www.agner.org/optimize/instruction_tables.pdf). Here are some samples values for my Zen 2 (all specified for 32-bit operands, if there is any difference):

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

Some comments:

- Because our minds are so used to the cost model where "more" means "worse", people mostly use *reciprocals* of throughput instead of throughput.
- If a certain instruction is especially frequent, its execution unit could be duplicated to increase its throughput — possibly to even more than one, but not higher than the [decode width](/hpc/architecture/layout).
- Some instructions have a latency of 0. This means that these instruction are used to control the scheduler and don't reach the execution stage. They still have non-zero reciprocal throughput because the [CPU front-end](/hpc/architecture/layout) still needs to process them.
- Most instructions are pipelined, and if they have the reciprocal throughput of $n$, this usually means that their execution unit can take another instruction after $n$ cycles (and if it is below 1, this means that there are multiple execution units, all capable of taking another instruction on the next cycle). One notable exception is the [integer division](/hpc/arithmetic/division): it is either very poorly pipelined or not pipelined at all.
- Some instructions have variable latency, depending on not only the size, but also the values of the operands. For memory operations (including fused ones like `add`), latency is usually specified for the best case (an L1 cache hit).

There are many more important little details, but this mental model will suffice for now.

<!--

This mental model covers 80% of your needs.

Some instruction tables also list execution ports (or sometimes "pipes"). This is mostly relevant for SIMD.

This is a bit of an advanced and not well understood topic. Documentation is very obscure. people have to reverse engineer it. There are reasons to believe that folks at Intel don't know that themselves. The most comprehensive one is probably, uops.info.

There are tools like llvm-mca, but they aren't perfect either.

-->

### An Education Analogy

Consider how our education system works:

1. Topics are taught to groups of students instead of individuals as broadcasting the same things to everyone at once is more efficient.
2. An intake of students is split into groups lead by different teachers; assignments and other course materials are shared between groups.
3. Each year the same course is taught to a new intake so that the teachers are kept busy.

These innovations greatly increase the *throughput* of the whole system, although the *latency* (time to graduation for a particular student) remains unchanged (and maybe increases a little bit because personalized tutoring is more effective).

You can find many analogies with modern CPUs:

1. CPUs use [SIMD parallelism](/hpc/simd) to execute the same operation on a block of different data points (comprised of 16, 32, or 64 bytes).
2. There are multiple execution units that can process these instructions simultaneously while sharing other CPU facilities (usually 2-4 execution units).
3. Instructions are processed in pipelined fashion (saving roughly the same number of cycles as the number of years between kindergarten and PhD).

<!-- You can continue "up": there are multiple school branches (cores), multiple schools (computers), etc. -->

In addition to that, several other aspects also match:

- Execution paths become more divergent with time and need different execution units.
- Some instructions may be stalled for various reasons.
- Some instructions are even speculated (executed ahead of time), but then discarded.
- Some instructions may be split in several distinct micro-operations that can proceed on their own.

Programming pipelined and superscalar processors presents its own challenges, which we are going to address in this chapter.
