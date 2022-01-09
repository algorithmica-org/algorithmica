---
title: Assembly Idioms
weight: 10
---

Lastly, there are a few "WTF is this" idioms in assembly language that felt wrong not to include in this chapter:

- The `lea` ("load effective address") instruction performs memory addressing and stores the address itself in a register without doing any memory operations. While its intended usage if to get addresses of class fields, it is often used as a trick that would otherwise involve 1 multiplication and 2 additions. For example, you can multiply by 3, 5 and 9 with it.
- `test rax, rax` is the optimal way to check if a value is zero. `test` instruction `and`s two values and sets flags according to the result. You can use `cmp rax, 0`, but it's machine code is one byte longer. This also implies that checking if a signed integer is exactly zero is slightly faster than checking if it is larger than zero.
- Likewise, `xor rax, rax` is the fastest way to set a register to zero.
- `xchg rax, rax` swaps a register with itself, and it is the official way to do nothing: `nop` maps to the same machine code. You may want to insert these operations to pad other instructions to specific addresses for a better memory layout, and we will talk about it in the next chapters.

If you think that this is hacky, unnatural and should be simplified, remember that just one level of abstraction away there is literally a rock that we tricked into thinking.
