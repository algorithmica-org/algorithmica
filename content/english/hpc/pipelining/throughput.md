---
title: Throughput Computing
weight: 4
---

Optimizing for *latency* is usually quite different from optimizing for *throughput*:

- When optimizing data structure queries or small one-time or branchy algorithms, you need to [look up the latencies](../tables) of its instructions, mentally construct the execution graph of the computation, and then try to reorganize it so that the critical path is shorter. <!-- [Binary GCD](/hpc/algorithms/gcd) is a good example of that. -->
- When optimizing hot loops and large-dataset algorithms, you need to look up the throughputs of their instructions, count how many times each one is used per iteration, determine which of them is the bottleneck, and then try to restructure the loop so that it is used less often.

The last advice only works for *data-parallel* loops, where each iteration is fully independent of the previous one. When there is some interdependency between consecutive iterations, there may potentially be a pipeline stall caused by a [data hazard](../hazards) as the next iteration is waiting for the previous one to complete.

### Example

As a simple example, consider how the sum of an array is computed:

```c++
int s = 0;

for (int i = 0; i < n; i++)
    s += a[i];
```

Let's assume for a moment that the compiler doesn't [vectorize](/hpc/simd) this loop, [the memory bandwidth](/hpc/cpu-cache/bandwidth) isn't a concern, and that the loop is [unrolled](/hpc/architecture/loops) so that we don't pay any additional cost associated with maintaining the loop variables. In this case, the computation becomes very simple:

```c++
int s = 0;
s += a[0];
s += a[1];
s += a[2];
s += a[3];
// ...
```

How fast can we compute this? At exactly one cycle per element — because we need one cycle each iteration to `add` another value to `s`. The latency of the memory read doesn't matter because the CPU can start it ahead of time.

But we can go higher than that. The *throughput* of `add`[^throughput] is 2 on my CPU (Zen 2), meaning we could theoretically execute two of them every cycle. But right now this isn't possible: while `s` is being used to accumulate $i$-th element, it can't be used for $(i+1)$-th for at least one cycle.

[^throughput]: The throughput of register-register `add` is 4, but since we are reading its second operand from memory, it is bottlenecked by the throughput of memory `mov`, which is 2 on Zen 2.

The solution is to use *two* accumulators and just sum up odd and and even elements separately:

```c++
int s0 = 0, s1 = 0;
s0 += a[0];
s1 += a[1];
s0 += a[2];
s1 += a[3];
// ...
int s = s0 + s1;
```

Now our superscalar CPU can execute these two "threads" simultaneously, and our computation no longer has any critical paths that limit the throughput.

<!--

By the virtue of out-of-order execution

-->

### The General Case

If an instruction has a latency of $x$ and a throughput of $y$, then you would need to use $x \cdot y$ accumulators to saturate it. This also implies that you need $x \cdot y$ logical registers to hold their values, which is an important consideration for CPU designs, limiting the maximum number of usable execution units for high-latency instructions.

This technique is mostly used with [SIMD](/hpc/simd) and not in scalar code. You can [generalize](/hpc/simd/reduction) the code above and compute sums and other reductions faster than the compiler.

In general, when optimizing loops, you usually have just one or a few *execution ports* that you want to utilize to their fullest, and you engineer the rest of the loop around them. As different instructions may use different sets of ports, it is not always clear which one is going to be overused. In situations like this, [machine code analyzers](/hpc/profiling/mca) can be very helpful for finding the bottlenecks of small assembly loops.

<!--

Compilers don't always produce the optimal code.

This only applies to the variables that you have to preserve between iterations. You can "fire and forget" instructions that compute temporary values as much as you want.

Memory operations may have [very high latencies](/hpc/cpu-cache/latency), but you don't need hundreds or registers for them because  because they are bottlenecked for different reasons.

But they are bottlenecked for different reasons.

You still need to imaging execution graph, but now loop it around. In most cases, there is one instruction that is the bottleneck.

This is different. For single-invocation procedures you essentially want to minimize the latency on the critical data path. For stuff that gets called in a loop, you need to maximize throughput.

Bandwidth is the rate at which data can be read or stored. For the purpose of designing algorithms, a more important characteristic is the bandwidth-latency product which basically tells how many cache lines you can request while waiting for the first one without queueing up. It is around 5 or more on most systems. This is like having friends whom you can send for beers asynchronously.

In the previous version, we have an inherently sequential chain of operations in the innermost loop. We accumulate the minimum in variable v by a sequence of min operations. There is no way to start the second operation before we know the result of the first operation; there is no room for parallelism here:

The result will be clearly the same, but we are calculating the operations in a different order. In essence, we split the work in two independent parts, calculating the minimum of odd elements and the minimum of even elements, and finally combining the results. If we calculate the odd minimum v0 and even minimum v1 in an interleaved manner, as shown above, we will have more opportunities for parallelism. For example, the 1st and 2nd operation could be calculated simultaneously in parallel (or they could be executed in a pipelined fashion in the same execution unit). Once these results are available, the 3rd and 4th operation could be calculated simultaneously in parallel, etc. We could potentially obtain a speedup of a factor of 2 here, and naturally the same idea could be extended to calculating, e.g., 4 minimums in an interleaved fashion.

Instruction-level parallelism is automatic Now that we know how to reorganize calculations so that there is potential for parallelism, we will need to know how to realize the potential. For example, if we have these two operations in the C++ code, how do we tell the computer that the operations can be safely executed in parallel?

The delightful answer is that it happens completely automatically, there is nothing we need to do (and nothing we can do)!

-->
