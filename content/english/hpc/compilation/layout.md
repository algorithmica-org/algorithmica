---
title: Machine Code Layout
weight: 10
---

front-end of a CPU

Instructions are encoded with a variable number of bytes.

align instructions

- `xchg rax, rax` swaps a register with itself, and it is the official way to do nothing: `nop` maps to the same machine code. You may want to insert these operations to pad other instructions to specific addresses for a better memory layout, and we will talk about it in the next chapters.

If you think that this is hacky, unnatural and should be simplified, remember that just one level of abstraction away there is literally a rock that we tricked into thinking.
