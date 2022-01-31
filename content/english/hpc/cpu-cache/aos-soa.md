---
title: AoS and SoA
weight: 12
---

Exploit [spatial locality](/hpc/external-memory/locality).

Let's modify the pointer chasing code so that the next pointer needs to be computed using a variable number of fields. We can either place them in separate arrays, or in the same array.

The first approach, struct

```c++
const int M = N / D; // # of memory accesses
int p[M], q[M][D];

iota(p, p + M, 0);
random_shuffle(p, p + M);

int k = p[M - 1];

for (int i = 0; i < M; i++)
    q[k][0] = p[i];

    for (int j = 1; j < D; j++)
        q[i][0] ^= (q[j][i] = rand());

    k = q[k][0];
}

for (int i = 0; i < M; i++) {
    int x = 0;
    for (int j = 0; j < D; j++)
        x ^= q[k][j];
    k = x;
}
```

Transpose the array and also swap indices in all its accesses:

```c++
int q[D][M];
//    ^--^
```

![](../img/aos-soa.svg)

Running a bit forward: the spikes at powers of two for AoS are due to SIMD, and dips in SoA are due to cache associativity.

### RAM-Specific Timings

![](../img/ram.png)

```c++
struct padded_int {
    int val;
    int padding[15];
};

const int M = N / D / 16;
padded_int q[M][D];
```

![](../img/aos-soa-padded.svg)

![](../img/aos-soa-padded-n.svg)

The rest of the core is the same: the only difference is that they require a separate cache line access.

This is only specific to RAM: on array sizes that fit in cache, the benchmark is actually worse because the [cache sharing is worse](../cache-lines).

RAM timings.

This isn't about $D$ being equal to 64 but about $\lfloor \frac{N}{D} \rfloor$ being a large power of two.

TODO fix D and change N

### Temporary Storage Contention

We can turn on hugepages, and they make it 10 times worse (notice the logarithmic scale):

![](../img/soa-hugepages.svg)

This is a rare example where hugepages actually worsen performance. Usually they the latency by 10-15%, but here they make it 10x worse.
