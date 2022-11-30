---
title: Machine Code Analyzers
weight: 4
---

A *machine code analyzer* is a program that takes a small snippet of assembly code and [simulates](../simulation) its execution on a particular microarchitecture using information available to compilers, and outputs the latency and throughput of the whole block, as well as cycle-perfect utilization of various resources within the CPU.

### Using `llvm-mca`

There are many different machine code analyzers, but I personally prefer `llvm-mca`, which you can probably install via a package manager together with `clang`. You can also access it through a web-based tool called [UICA](https://uica.uops.info) or in the [Compiler Explorer](https://godbolt.org/) by selecting "Analysis" as the language.

What `llvm-mca` does is it runs a set number of iterations of a given assembly snippet and computes statistics about the resource usage of each instruction, which is useful for finding out where the bottleneck is.

We will consider the array sum as our simple example:

```asm
loop:
    addl (%rax), %edx
    addq $4, %rax
    cmpq %rcx, %rax
    jne	 loop
````

Here is its analysis with `llvm-mca` for the Skylake microarchitecture:

```yaml
Iterations:        100
Instructions:      400
Total Cycles:      108
Total uOps:        500

Dispatch Width:    6
uOps Per Cycle:    4.63
IPC:               3.70
Block RThroughput: 0.8
```

First, it outputs general information about the loop and the hardware:

- It "ran" the loop 100 times, executing 400 instructions in total in 108 cycles, which is the same as executing $\frac{400}{108} \approx 3.7$ [instructions per cycle](/hpc/complexity/hardware) on average (IPC).
- The CPU is theoretically capable of executing up to 6 instructions per cycle ([dispatch width](/hpc/architecture/layout)).
- Each cycle in theory can be executed in 0.8 cycles on average ([block reciprocal throughput](/hpc/pipelining/tables)).
- The "uOps" here are the micro-operations that the CPU splits each instruction into (e.g., fused load-add is composed of two uOps).

Then it proceeds to give information about each individual instruction: 

```yaml
Instruction Info:
[1]: uOps
[2]: Latency
[3]: RThroughput
[4]: MayLoad
[5]: MayStore
[6]: HasSideEffects (U)

[1]    [2]    [3]    [4]    [5]    [6]    Instructions:
 2      6     0.50    *                   addl	(%rax), %edx
 1      1     0.25                        addq	$4, %rax
 1      1     0.25                        cmpq	%rcx, %rax
 1      1     0.50                        jne	-11
```

There is nothing there that there isn't in the [instruction tables](/hpc/pipelining/tables):

- how many uOps each instruction is split into;
- how many cycles each instruction takes to complete (latency);
- how many cycles each instruction takes to complete in the amortized sense (reciprocal throughput), considering that several copies of it can be executed simultaneously.

Then it outputs probably the most important part — which instructions are executing when and where:

```yaml
Resource pressure by instruction:
[0]    [1]    [2]    [3]    [4]    [5]    [6]    [7]    [8]    [9]    Instructions:
 -      -     0.01   0.98   0.50   0.50    -      -     0.01    -     addl (%rax), %edx
 -      -      -      -      -      -      -     0.01   0.99    -     addq $4, %rax
 -      -      -     0.01    -      -      -     0.99    -      -     cmpq %rcx, %rax
 -      -     0.99    -      -      -      -      -     0.01    -     jne  -11
```

As the contention for execution ports causes [structural hazards](/hpc/pipelining/hazards), ports often become the bottleneck for throughput-oriented loops, and this chart helps diagnose why. It does not give you a cycle-perfect Gantt chart of something like that, but it gives you the aggregate statistics of the execution ports used for each instruction, which lets you find which one is overloaded.

<!--

A CPU is a very complicated thing, but in essence, there are several "ports" that specialize on particular kinds of instructions. These ports often become the bottleneck, and the chart above helps in diagnosing why.

We are not ready to discuss how this works yet, but will talk about it in detail in the last chapter.

-->
