---
title: Memory-Level Parallelism
weight: 3
---

- Memory requests can overlap in time: while you wait for a read request to complete, you can sand a few others, which will be executed concurrently. In some contexts that allow for many concurrent I/O operations it therefore makes more sense to talk abound memory *bandwidth* than *latency*.

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

![](../img/permutation-mlp.svg)

There is a conflict over registers:

```nasm
dec     edx
movsx   rdi, DWORD PTR q[0+rdi*4]
movsx   rsi, DWORD PTR q[1048576+rsi*4]
movsx   rcx, DWORD PTR q[2097152+rcx*4]
movsx   rax, DWORD PTR q[3145728+rax*4]
jne     .L9
```

```nasm
mov     edx, DWORD PTR q[0+rdx*4]
mov     DWORD PTR [rbp-128+rax*4], edx
```

### AoS and SoA

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