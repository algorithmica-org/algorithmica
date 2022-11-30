---
title: Memory-Level Parallelism
weight: 5
---

Memory requests can overlap in time: while you wait for a read request to complete, you can send a few others, which will be executed concurrently with it. This is the main reason why [linear iteration](../bandwidth) is so much faster than [pointer jumping](../latency): the CPU knows which memory locations it needs to fetch next and sends memory requests far ahead of time.

The number of concurrent memory operations is large but limited, and it is different for different types of memory. When designing algorithms and especially data structures, you may want to know this number, as it limits the amount of parallelism your computation can achieve.

To find this limit theoretically for a specific memory type, you can multiply its latency (time to fetch a cache line) by its bandwidth (number of cache lines fetched per second), which gives you the average number of memory operations in progress:

![](../img/latency-bandwidth.svg)

The latency of the L1/L2 caches is small, so there is no need for a long pipeline of pending requests, but larger memory types can sustain up to 25-40 concurrent read operations.

### Direct Experiment

Let's try to measure available memory parallelism more directly by modifying our pointer chasing benchmark so that we loop around $D$ separate cycles in parallel instead of just one: 

```c++
const int M = N / D;
int p[M], q[D][M];

for (int d = 0; d < D; d++) {
    iota(p, p + M, 0);
    random_shuffle(p, p + M);
    k[d] = p[M - 1];
    for (int i = 0; i < M; i++)
        k[d] = q[d][k[d]] = p[i];
}

for (int i = 0; i < M; i++)
    for (int d = 0; d < D; d++)
        k[d] = q[d][k[d]];
```

Fixing the sum of the cycle lengths constant at a few select sizes and trying different $D$, we get slightly different results:

![](../img/permutation-mlp.svg)

The L2 cache run is limited by ~6 concurrent operations, as predicted, but larger memory types all max out between 13 and 17. You can't make use of more memory lanes as there is a conflict over logical registers. When the number of lanes is fewer than the number of registers, you can issue just one read instruction per lane:

```nasm
dec     edx
movsx   rdi, DWORD PTR q[0+rdi*4]
movsx   rsi, DWORD PTR q[1048576+rsi*4]
movsx   rcx, DWORD PTR q[2097152+rcx*4]
movsx   rax, DWORD PTR q[3145728+rax*4]
jne     .L9
```

But when it is over ~15, you have to use temporary memory storage:

```nasm
mov     edx, DWORD PTR q[0+rdx*4]
mov     DWORD PTR [rbp-128+rax*4], edx
```

You don't always get to the maximum possible level of memory parallelism, but for most applications, a dozen concurrent requests are more than enough.
