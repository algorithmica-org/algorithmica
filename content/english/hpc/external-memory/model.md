---
title: External Memory Model
weight: 3
---

To reason about the performance of memory-bound algorithms, we need to develop a cost model that is more sensitive to expensive block I/O operations but is not too rigorous to still be useful.

### Cache-Aware Model

In the [standard RAM model](/hpc/complexity), we ignore the fact that primitive operations take unequal time to complete. Most importantly, it does not differentiate between operations on different types of memory, equating a read from RAM taking ~50ns in real-time with a read from HDD taking ~5ms, or about a $10^5$ times as much.

Similar in spirit, in the *external memory model*, we simply ignore every operation that is not an I/O operation. More specifically, we consider one level of cache hierarchy and assume the following about the hardware and the problem:

- The size of the dataset is $N$, and it is all stored in *external* memory, which we can read and write in blocks of $B$ elements in a unit time (reading a whole block and just one element takes the same time).
- We can store $M$ elements in *internal* memory, meaning that we can store up to $\left \lfloor \frac{M}{B} \right \rfloor$ blocks.
- We only care about I/O operations: any computations done in-between the reads and the writes are free.
- We additionally assume $N \gg M \gg B$.

In this model, we measure the performance of an algorithm in terms of its high-level *I/O operations*, or *IOPS* — that is, the total number of blocks read or written to external memory during execution.

We will mostly focus on the case where the internal memory is RAM and the external memory is SSD or HDD, although the underlying analysis techniques that we will develop are applicable to any layer in the cache hierarchy. Under these settings, reasonable block size $B$ is about 1MB, internal memory size $M$ is usually a few gigabytes, and $N$ is up to a few terabytes.

### Array Scan

<!-- The external memory model can be used very efficiently without sacrificing simplicity. -->

As a simple example, when we calculate the sum of an array by iterating through it one element at a time, we implicitly load it by chunks of $O(B)$ elements and, in terms of the external memory model, process these chunks one by one:

$$
\underbrace{a_1, a_2, a_3,} _ {B_1}
\underbrace{a_4, a_5, a_6,} _ {B_2}
\ldots
\underbrace{a_{n-3}, a_{n-2}, a_{n-1}} _ {B_{m-1}}
$$

Thus, in the external memory model, the complexity of summation and other linear array scans is

$$
SCAN(N) \stackrel{\text{def}}{=} O\left(\left \lceil \frac{N}{B} \right \rceil \right) \; \text{IOPS}
$$

You can implement external array scan explicitly like this:

```c++
FILE *input = fopen("input.bin", "rb");

const int M = 1024;
int buffer[M], sum = 0;

// while the file is not fully processed
while (true) {
    // read up to M of 4-byte elements from the input stream
    int n = fread(buffer, 4, M, input);
    //  ^ the number of elements that were actually read

    // if we can't read any more elements, finish
    if (n == 0)
        break;
    
    // sum elements in-memory
    for (int i = 0; i < n; i++)
        sum += buffer[i];
}

fclose(input);
printf("%d\n", sum);
```

Note that, in most cases, operating systems do this buffering automatically. Even when the data is just redirected to the standard input from a normal file, the operating system buffers its stream and reads it in blocks of ~4KB (by default).
