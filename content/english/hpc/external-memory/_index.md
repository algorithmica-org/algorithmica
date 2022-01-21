---
title: External Memory
weight: 8
---

If a CPU core has a frequency of 3 GHz, it roughly means that it is capable of executing up to $3 \cdot 10^9$ operations per second, depending on what constitutes an "operation". This is the baseline: on modern architectures, it can be increased by techniques such as SIMD and instruction-level parallelism up to $10^{11}$ operations per second, if the computation allows it.

But for many algorithms, the CPU is not the bottleneck. Before trying to optimize performance above that baseline, we need to learn not to drop below it, and the number one reason for this is memory.

## A + B

To illustrate this point, consider this: how long does it take to add two numbers together? The only correct answer to this question is "it depends" — mainly on where the operands are stored.

Being one of the most frequently used instructions, `add` by itself only takes one cycle to execute. So if the data is already in registers, it takes one cycle. In general case (`*c = *a + *b`), it needs to fetch its operands from memory first:

```nasm
mov eax, DWORD PTR [rsi]
add eax, DWORD PTR [rdi]
mov DWORD PTR [rdx], eax
```

Typically, the data is stored in the main memory (RAM), and it will take around ~40ns, or about 100 cycles, to fetch it, and then another 100 cycles to write it back. If it was accessed recently, it is probably *cached* and will take less than that to fetch, depending on how long ago it was accessed — it could be ~20ns for the slowest layer of cache and under 1ns for the fastest. But it could also be that the data is stored on the hard drive, and in this case it will take around 5ms, or roughly $10^7$ cycles (!), to access it.

Because of such a high variance in performance, it is crucial to optimize IO operations before anything else.
