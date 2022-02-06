---
title: Masking and Blending
weight: 4
---

One of the bigger challenges of SIMD programming is that its options for control flow are very limited — because the operations you apply to a vector are the same for all its elements.

This makes the problems that are usually trivially resolved with an `if` or any other type of branching much harder. With SIMD, they have to be dealt with by the means of various [branchless programming](/hpc/pipelining/branchless) techniques, which aren't always that straightforward to apply.

### Masking

The main way to make a computation branchless is through *predication* — computing the results of both branches and then using either some arithmetic trick or a special "conditional move" instruction:

```c++
for (int i = 0; i < N; i++)
    a[i] = rand() % 100;

int s = 0;

// branch:
for (int i = 0; i < N; i++)
    if (a[i] < 50)
        s += a[i];

// no branch:
for (int i = 0; i < N; i++)
    s += (a[i] < 50) * a[i];

// also no branch:
for (int i = 0; i < N; i++)
    s += (a[i] < 50 ? a[i] : 0);
```

To vectorize this loop, we are going to need two new instructions:

- `_mm256_cmpgt_epi32`, which compares the integers in two vectors and produces a mask of all ones if the first element is more than the second and a mask of full zeros otherwise.
- `_mm256_blendv_epi8`, which blends (combines) the values of two vectors based on the provided mask.

By masking and blending the elements of a vector so that only the selected subset of them is affected by computation, we can perform predication in a manner similar to the conditional move:

```c++
const reg c = _mm256_set1_epi32(49);
const reg z = _mm256_setzero_si256();
reg s = _mm256_setzero_si256();

for (int i = 0; i < N; i += 8) {
    reg x = _mm256_load_si256( (reg*) &a[i] );
    reg mask = _mm256_cmpgt_epi32(x, c);
    x = _mm256_blendv_epi8(x, z, mask);
    s = _mm256_add_epi32(s, x);
}
```

(Minor details such as [horizontal summation and accounting for the remainder of the array](../reduction) are omitted for brevity.)

This is how predication is usually done in SIMD, but it isn't always the most optimal approach. We can use the fact that one of the blended values is zero, and use bitwise `and` with the mask instead of blending:

```c++
const reg c = _mm256_set1_epi32(50);
reg s = _mm256_setzero_si256();

for (int i = 0; i < N; i += 8) {
    reg x = _mm256_load_si256( (reg*) &a[i] );
    reg mask = _mm256_cmpgt_epi32(c, x);
    x = _mm256_and_si256(x, mask);
    s = _mm256_add_epi32(s, x);
}
```

This loop performs slightly faster because on this particular CPU, the vector `and` take one cycle less than `blend`.

Several other instructions support masks as inputs, most notably:

- The `_mm256_blend_epi32` intrinsic is a `blend` that takes an 8-bit integer mask instead of a vector (which is why it doesn't have `v` at the end).
- The `_mm256_maskload_epi32` and `_mm256_maskstore_epi32` intrinsics that load/store a SIMD block from memory and `and` it with a mask in one go.

We can also use predication with built-in vector types:

```c++
vec *v = (vec*) a;
vec s = {};

for (int i = 0; i < N / 8; i++)
    s += (v[i] < 50 ? v[i] : 0);
```

All these versions work at around 13 GFLOPS as this example is so simple that the compiler can vectorize the loop all by itself. Let's move on to more complex examples that can't be auto-vectorized.

### Searching

In the next example, we need to find a specific value in an array and return its position:

```c++
const int N = (1<<12);
int a[N];

int find(int x) {
    for (int i = 0; i < N; i++)
        if (a[i] == x)
            return i;
    return -1;
}
```

To benchmark the `find` function, we fill the array with numbers from $0$ to $(N - 1)$ and then repeatedly search for a random element:

```c++
for (int i = 0; i < N; i++)
    a[i] = i;

for (int t = 0; t < K; t++)
    checksum ^= find(rand() % N);
```

The scalar version gives ~4 GFLOPS of performance. This number includes the elements we haven't had to process, so divide this number by two in your head (the expected fraction of the elements we have to check).

To vectorize it, we need to compare a vector of its elements with the searched value for equality, producing a mask, and then somehow check if this mask is zero. If it isn't, the needed element is somewhere within this block of 8.

To check if the mask is zero, we can use the `_mm256_movemask_ps` intrinsic, which takes the first bit of each 32-bit element in a vector and produces an 8-bit integer mask out of them. We can then check if this mask is non-zero — and if it is, also immediately get the index with the `ctz` instruction:

```c++
int find(int needle) {
    reg x = _mm256_set1_epi32(needle);

    for (int i = 0; i < N; i += 8) {
        reg y = _mm256_load_si256( (reg*) &a[i] );
        reg m = _mm256_cmpeq_epi32(x, y);
        int mask = _mm256_movemask_ps((__m256) m);
        if (mask != 0)
            return i + __builtin_ctz(mask);
    }

    return -1;
}
```

This version gives ~20 GFLOPS or about 5 times faster than the scalar one. It only uses 3 instructions in the hot loop:

```nasm
vpcmpeqd  ymm0, ymm1, YMMWORD PTR a[0+rdx*4]
vmovmskps eax, ymm0
test      eax, eax
je        loop
```

Checking if a vector is zero is a common operation, and there is an operation similar to `test` in SIMD that we can use:

```c++
int find(int needle) {
    reg x = _mm256_set1_epi32(needle);

    for (int i = 0; i < N; i += 8) {
        reg y = _mm256_load_si256( (reg*) &a[i] );
        reg m = _mm256_cmpeq_epi32(x, y);
        if (!_mm256_testz_si256(m, m)) {
            int mask = _mm256_movemask_ps((__m256) m);
            return i + __builtin_ctz(mask);
        }
    }

    return -1;
}
```

We are still using `movemask` to do `ctz` later, but the hot loop is now one instruction shorter:

```nasm
vpcmpeqd ymm0, ymm1, YMMWORD PTR a[0+rdx*4]
vptest   ymm0, ymm0
je       loop
```

This doesn't improve performance much on this particular architecture as the `movemask` wasn't the bottleneck.

### Counting Values

As the final exercise, let's find the count of a value in an array instead of just its first occurrence:

```c++
int count(int x) {
    int cnt = 0;
    for (int i = 0; i < N; i++)
        cnt += (a[i] == x);
    return cnt;
}
```

To vectorize it, we just need to convert the comparison mask to either one or zero per element and calculate the sum:

```c++
const reg ones = _mm256_set1_epi32(1);

int count(int needle) {
    reg x = _mm256_set1_epi32(needle);
    reg s = _mm256_setzero_si256();

    for (int i = 0; i < N; i += 8) {
        reg y = _mm256_load_si256( (reg*) &a[i] );
        reg m = _mm256_cmpeq_epi32(x, y);
        m = _mm256_and_si256(m, ones);
        s = _mm256_add_epi32(s, m);
    }

    return hsum(s);
}
```

Both implementations yield ~15 GFLOPS: the compiler can vectorize the first one all by itself.

But a trick that the compiler can't find is to notice that the mask of all ones is [minus one](/hpc/arithmetic/integer) when reinterpreted as an integer. So we can skip the and-the-lowest-bit part and use the mask itself, and then just negate the final result:

```c++
int count(int needle) {
    reg x = _mm256_set1_epi32(needle);
    reg s = _mm256_setzero_si256();

    for (int i = 0; i < N; i += 8) {
        reg y = _mm256_load_si256( (reg*) &a[i] );
        reg m = _mm256_cmpeq_epi32(x, y);
        s = _mm256_add_epi32(s, m);
    }

    return -hsum(s);
}
```

This doesn't improve the performance in this particular architecture because the throughput is actually bottlenecked by updating `s`: there is a dependency on the previous iteration, so the loop can't proceed faster than one iteration per CPU cycle. We can make use of [instruction-level parallelism](../reduction#instruction-level-parallelism) if we split the accumulator in two:

```c++
int count(int needle) {
    reg x = _mm256_set1_epi32(needle);
    reg s1 = _mm256_setzero_si256();
    reg s2 = _mm256_setzero_si256();

    for (int i = 0; i < N; i += 16) {
        reg y1 = _mm256_load_si256( (reg*) &a[i] );
        reg y2 = _mm256_load_si256( (reg*) &a[i + 8] );
        reg m1 = _mm256_cmpeq_epi32(x, y1);
        reg m2 = _mm256_cmpeq_epi32(x, y2);
        s1 = _mm256_add_epi32(s1, m1);
        s2 = _mm256_add_epi32(s2, m2);
    }

    s1 = _mm256_add_epi32(s1, s2);

    return -hsum(s1);
}
```

It now gives ~22 GFLOPS of performance, which is as high as it can get.

<!-- TODO: ILP first, -1 second -->
