---
title: Throughput Computing
weight: 4
---

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
