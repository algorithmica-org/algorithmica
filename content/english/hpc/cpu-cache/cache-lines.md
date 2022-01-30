---
title: Cache Lines
weight: 3
---

The basic units of data transfer in the CPU cache system are not individual bits and bytes, but *cache lines*. On most architectures, the size of a cache line is 64 bytes, meaning that all memory is divided in blocks of 64 bytes, and whenever you request (read or write) a single byte, you are also fetching all its 63 cache line neighbors whether your want them or not.

To demonstrate this, we add a "step" parameter to our [incrementing loop](../bandwidth). Now we only touch every $D$-th element:
 
```cpp
for (int i = 0; i < N; i += D)
    a[i]++;
```

If we run it with $D=1$ and $D=16$, we can observe something interesting:

![Performance is normalized by the total time to run benchmark, not the total number of elements incremented](../img/strided.svg)

As the problem size grows, the graphs of the two loops meet, despite one doing 16 times less work than the other. This is because, in terms of cache lines, we are fetching the exact same memory in both loops, and the fact that the strided loop only needs one-sixteenth of it is irrelevant.

When the array fits into the L1 cache, the strided version completes faster — although not 16 but just two times as fast. This is because it only needs to do half the work: it only executes a single `inc DWORD PTR [rdx]` instruction for every 16 elements, while the original loop needed two 8-element [vector instructions](/hpc/simd) to process the same 16 elements. Both computations are bottlenecked by writing the result back: Zen 2 can only write one word per cycle — regardless of whether it is composed of one integer or eight.

When we change the step parameter to 8, the graphs equalize, as we now also need two increments and two write-backs per every 16 elements:

![](../img/strided2.svg)

We can use this effect to minimize cache sharing in our [latency benchmark](../latency) to measure it more precisely. We need to *pad* the indices of a permutation so that each of them lies in its own cache line:

```c++
struct padded_int {
    int val;
    int padding[15];
};

padded_int q[N / 16];

// constructing a cycle from a random permutation
// ...

for (int i = 0; i < N / 16; i++)
    k = q[k].val;
```

Now, each index is much more likely to be kicked out of the cache by the time we loop around and request it again:

![](../img/permutation-padded.svg)

The important practical lesson when designing and analyzing memory-bound algorithms is to count the number of cache lines accessed and not just the total count of memory reads and writes.
