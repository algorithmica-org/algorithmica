---
title: Machine Code Layout
weight: 10
---

Machine instructions are encoded using variable amount of bytes: something simple and very common like `inc rax` takes one byte, while some obscure instruction with encoded constants and behavior-modifying prefixes may take up to 15.

It is called the "front-end" of a CPU.

In streams of 16 bytes. However full instructions are there (but no more than the decode width) are going to the next stage.

Optimizations such as inlining and loops unrolling

There is a separate cache for instructions. Binaries can get big pretty fast,

Align calls by inserting no-ops.

front-end of a CPU

Instructions are encoded with a variable number of bytes.

align instructions

- `xchg rax, rax` swaps a register with itself, and it is the official way to do nothing: `nop` maps to the same machine code. You may want to insert these operations to pad other instructions to specific addresses for a better memory layout, and we will talk about it in the next chapters.
