---
title: Cache-Aware Model
weight: 3
---

To reason about performance of memory-bound algorithms, we need to develop a cost model that is more sensitive to expensive block IO operations, but is not too rigorous to still be useful.

In the standard RAM model, we ignore the fact that primitive operations take unequal time to complete. Most importantly, it does not differentiate between operations on different types of memory, equating a read from RAM taking ~50ns in real-time with a read from HDD taking ~5ms, or about a $10^5$ times as much.

Similar in spirit, in *external memory model*, we simply ignore every operation that is not an I/O operation. More specifically, we consider one level of cache hierarchy and assume the following about the hardware and the problem:

- The size of the dataset is $N$, and it is all stored in *external* memory, which we can read and write in blocks of $B$ elements in a unit time (reading a whole block and just one element takes the same time).
- We can store $M$ elements in *internal* memory, meaning that we can store up to $\left \lfloor \frac{M}{B} \right \rfloor$ blocks.
- We only care about I/O operations: any computations done in-between reads and writes are free.
- We additionally assume $N \gg M \gg B$.

In this model, we measure performance of the algorithm in terms of its high-level *I/O operations*, or *IOPS* — that is, the total number of blocks read or written to external memory during execution.

We will mostly focus on the case where the internal memory is RAM and external memory is SSD or HDD, although the underlying analysis techniques that we will develop are applicable to any layer in the cache hierarchy. Under these settings, reasonable block size $B$ is about 1MB, internal memory size $M$ is usually a few gigabytes, and $N$ is up to a few terabytes.

## Array Scan

<!-- The external memory model can be used very efficiently without sacrificing simplicity. -->

As a simple example, when we calculate the sum of array by iterating through it one element at a time, we implicitly load it by chunks of $O(B)$ elements and, in terms of external memory model, process these chunks one by one:

$$
\underbrace{a_1, a_2, a_3,} _ {B_1}
\underbrace{a_4, a_5, a_6,} _ {B_2}
\ldots
\underbrace{a_{n-3}, a_{n-2}, a_{n-1}} _ {B_{m-1}}
$$

Thus, in external memory model, the complexity of summation and other linear array scans is

$$
SCAN(N) \stackrel{\text{def}}{=} O\left(\left \lceil \frac{N}{B} \right \rceil \right) \; \text{IOPS}
$$

Note that, in most cases, operating systems do this automatically. Even when the data is just redirected to the standard input from a normal file, the operating system buffers its stream and reads it in blocks of ~4KB (by default).

<!-- code with explicit bufferization of input with fread -->

Now, let's slowly build up more complex things. The goal of this article is to eventually get to *external sorting* and its interesting applications. It will be based on the standard merge sort, so we need to derive a few of its primitives first.
