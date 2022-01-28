---
title: AoS and SoA
weight: 4
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

Running a bit forward: the boosts at powers of two for AoS are due to SIMD, and dips in SoA are due to cache associativity.

<!-- TODO: aos, but padded -->
