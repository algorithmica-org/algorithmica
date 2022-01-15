---
title: Throughput Computing
weight: 4
---

Optimizing for latency is quite different from optimizing for throughput.

- You need to imagine the execution graph with its latencies and try to make it shorter. In most cases it just means finding the critical path and trying to get rid of it. [Binary GCD](/hpc/algorithms/gcd) is a good example of that.
- You still need to imaging execution graph, but now loop it around. In most cases, there is one instruction that is the bottleneck.

There are some examples where both are relevant, but in general you are bottlenecked either by latency or bandwidth.

Loops are usually good examples. Consider the problem of computing an array sum.

The same thing you could repeat for [SIMD](/hpc/simd/reduction). And in fact, compilers aren't always able to produce optimal code for this case.

Convert to scalar code. Link to SIMD example of reduction.

This is different. For single-invocation procedures you essentially want to minimize the latency on the critical data path. For stuff that gets called in a loop, you need to maximize throughput.

Bandwidth is the rate at which data can be read or stored. For the purpose of designing algorithms, a more important characteristic is the bandwidth-latency product which basically tells how many cache lines you can request while waiting for the first one without queueing up. It is around 5 or more on most systems. This is like having friends whom you can send for beers asynchronously.

```c++
int ilp_sum_v2() {
    vec b[B] = {0};
    vec* v = (vec*) a;

    for (int i = 0; i < N/8; i += B)
        for (int j = 0; j < B; j++)
            b[j] += v[i + j];
    
    for (int i = 1; i < B; i++)
        b[0] += b[i];
    
    int s = 0;

    for (int i = 0; i < 8; i++)
        s += b[0][i];

    return s;
}

```



In the previous version, we have an inherently sequential chain of operations in the innermost loop. We accumulate the minimum in variable v by a sequence of min operations. There is no way to start the second operation before we know the result of the first operation; there is no room for parallelism here:

...
v = std::min(v, z0);
v = std::min(v, z1);
v = std::min(v, z2);
v = std::min(v, z3);
v = std::min(v, z4);
...
Independent operations
There is a simple way to reorganize the operations so that we have more room for parallelism. Instead of accumulating one minimum, we could accumulate two minimums, and at the very end combine them:

...
v0 = std::min(v0, z0);
v1 = std::min(v1, z1);
v0 = std::min(v0, z2);
v1 = std::min(v1, z3);
v0 = std::min(v0, z4);
...

v = std::min(v0, v1);
The result will be clearly the same, but we are calculating the operations in a different order. In essence, we split the work in two independent parts, calculating the minimum of odd elements and the minimum of even elements, and finally combining the results. If we calculate the odd minimum v0 and even minimum v1 in an interleaved manner, as shown above, we will have more opportunities for parallelism. For example, the 1st and 2nd operation could be calculated simultaneously in parallel (or they could be executed in a pipelined fashion in the same execution unit). Once these results are available, the 3rd and 4th operation could be calculated simultaneously in parallel, etc. We could potentially obtain a speedup of a factor of 2 here, and naturally the same idea could be extended to calculating e.g. 4 minimums in an interleaved fashion.

Instruction-level parallelism is automatic
Now that we know how to reorganize calculations so that there is potential for parallelism, we will need to know how to realize the potential. For example, if we have these two operations in the C++ code, how do we tell the computer that the operations can be safely executed in parallel?


v0 = std::min(v0, z0);
v1 = std::min(v1, z1);
The delightful answer is that it happens completely automatically, there is nothing we need to do (and nothing we can do)!
