---
title: Machine Code Analyzers
weight: 4
---

The second category is *machine code analyzers*. These are programs that take assembly code and simulate its execution on a particular microarchitecture using information available to compilers, and output the latency and throughput of the whole snippet, as well as cycle-perfect utilization of various resources in a CPU.

There are many of them, but I personally prefer `llvm-mca`, which you can probably install via a package manager together with `clang`. You can also access it through a new web-based tool called [UICA](https://uica.uops.info).

### Machine Code Analyzers

What machine code analyzers do is they run a set number of iterations of a given assembly snippet and compute statistics about the resource usage of each instruction, which is useful for finding out where the bottleneck is.

We will consider the array sum as our simple example:

```asm
loop:
    addl (%rax), %edx
    addq $4, %rax
    cmpq %rcx, %rax
    jne	 loop
````

Here is its analysis with `llvm-mca` on Skylake. You are not going to understand much, but that's fine for now.

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

- It "ran" the loop 100 times, executing 400 instructions in total in 108 cycles, which is the same as executing $\frac{400}{108} \approx 3.7$ instructions per cycle ("IPC") on average.
- The CPU is theoretically capable of executing up to 6 instructions per cycle ("dispatch width").
- Each cycle in theory can be executed in 0.8 cycles on average ("block reciprocal throughput").
- The "uOps" here are the micro-operations that CPU splits each instruction into (e. g. fused load-add is composed of two uOps).

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

There is nothing there that there isn't in the instruction tables:

- how many uOps each instruction is split into;
- how many cycles each instruction takes to complete ("latency");
- how many cycles each instruction takes to complete in the amortized sense ("reciprocal throughput"), considering that several copies of it can be executed simultaneously.

Then it outputs probably the most important part — which instructions are executing when and where:

```yaml
Resource pressure by instruction:
[0]    [1]    [2]    [3]    [4]    [5]    [6]    [7]    [8]    [9]    Instructions:
 -      -     0.01   0.98   0.50   0.50    -      -     0.01    -     addl (%rax), %edx
 -      -      -      -      -      -      -     0.01   0.99    -     addq $4, %rax
 -      -      -     0.01    -      -      -     0.99    -      -     cmpq %rcx, %rax
 -      -     0.99    -      -      -      -      -     0.01    -     jne  -11
```

A CPU is a very complicated thing, but in essence, there are several "ports" that specialize on particular kinds of instructions. These ports often become the bottleneck, and the chart above helps in diagnosing why.

We are not ready to discuss how this works yet, but will talk about it in detail in the last chapter.
