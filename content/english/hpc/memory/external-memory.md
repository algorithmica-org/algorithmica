---
title: External Memory Model
weight: 1
draft: true
---

To reason about memory and not go crazy, we need a model that is more sensitive, yet not so rigorous.

In RAM model, we ignored the fact that primitive operations take unequal time.

But consider an algoritm that does something on the memory. Each access takes at least 10ms.

In these cases, we can use a different cost model without sacrificing simplicity: we ignore all computation except for I/O operations.

A bit informal description:

Consider one level in cache hierarchy. 
- Data size is $N$, it is stored in *external* memory, which we can read and write in blocks of $B$ elements in one unit time (reading a whole block and just one element takes the same time).
- We can store $M$ elements *internal* memory, meaning that we can store $\left \lfloor \frac{M}{B} \right \rfloor$ blocks.
- We only care about I/O: any computation done in-between reads and writes is free.
- We assume $N \gg M \gg B$

It is measured in *I/O operations* or *IOPS*.

## Array Scan

For example, when we calculate $\sum_i a_i$ by iterating through array, it takes $SCAN(N) \stackrel{\text{def}}{=} O(\left \lceil \frac{N}{B} \right \rceil)$ IOPS.

$$
\underbrace{a_1, a_2, a_3,} _ {B_1}
\underbrace{a_4, a_5, a_6,} _ {B_2}
\ldots
\underbrace{a_{n-3}, a_{n-2}, a_{n-1}} _ {B_{m-1}}
$$

One thing you need to consider is buffering. By the way, this is what happens with console input and output.

```cpp
int scan() {
    // some explicit implementation
}
```

When you are just working on the RAM level, it happens by default. Same thing with mmap-ed files.
