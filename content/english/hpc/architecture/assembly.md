---
title: Assembly Language
weight: 1
---

*Machine language* is just a stream of instructions encoded with some variable amount of bytes that specify

- the instruction number (called *opcode*),
- what its operands are,
- where to store the result.

A much more human friendly rendition of machine language, called *assembly language*, uses mnemonic codes to refer to machine code instructions and symbolic names to refer to registers and other storage locations.

Jumping right into it, here is how you add two numbers (`*c = *a + *b`) in arm assembly:

```nasm
; *a = x0, *b = x2, *c = x2
ldr w0, [x0]    ; load 4 bytes from wherever x0 points into w0
ldr w1, [x1]    ; load 4 bytes from wherever x1 points into w1
add w0, w0, w1  ; add w0 with w1 and save the result to w0
str w0, [x2]    ; write contents of w0 to wherever x2 points/
```

Here is the same operation in x86 assembly:

```nasm
; *a = rsi, *b = rdi, *c = rdx 
mov eax, DWORD PTR [rsi]  ; load 4 bytes from wherever rsi points into eax
add eax, DWORD PTR [rdi]  ; add whatever is stored at rdi to eax
mov DWORD PTR [rdx], eax  ; write contents of eax to wherever rdx points
```

Assembly is very simple in the sense that it doesn't have a lot of syntactical constructions compared to high-level programming languages. From what you can observe from the examples above:

- A program is a sequence of instructions, each written as its name followed by a variable amount of operands.
- The `[reg]` syntax is used for "dereferencing" a pointer stored in a register, and on x86 you need to prefix it with size information (`DWORD` here means 32 bit).
- The `;` sign is used for line comments, like `#` and `//` in other languages.

Assembly a very minimal language because it needs to be. It reflects the machine language as closely as possible, up to the point where there is almost 1:1 correspondence between machine code and assembly. In fact, you can turn any compiled program back into its assembly form by a process called *disassembly* — although everything non essential like comments will not be preserved.

Note that the two snippets above are not just syntactically different. Both are optimized codes produced by a compiler, but arm version uses 4 instruction, while x86 version uses 3. The `add eax, [rdi]` instruction is what's called *fused instruction* that does a load and an add in one go — this is one of the perks that CISC approach can provide.

Since there are far more differences between the architectures than just this one, from here on and until the rest of the book we will only provide examples for x86, which is probably what most of our readers will optimize for, although many of the introduced concepts will be architecture-agnostic.

### Instructions and Registers

Due to historical reasons, instruction mnemonics in most assembly languages are very terse. Back when people used to write assembly by hand and repeatedly wrote the same set of common instructions, one less character to type was one step away from insanity.

For example, `mov` is "copy a word", `inc` is "increment by 1" and `idiv` is "signed division". You can look up the description of an instruction by its name in [one of x86 references](https://www.felixcloutier.com/x86/), but most instructions do what you'd think they do.

Most instructions write their result into the first operand, which can also be involved in the computation like in the `add eax, [rdi]` example we saw before. Operands can be either constant values, registers or memory locations.

**Constants** are just integer or floating point values: `42`, `0x2a`, `3.14`, `6.02e23`. They are embedded right into the machine code. There are also string constants such as `hello` or `world\n` with their own little subset of operations, but that is a somewhat obscure corner of the assembly language that we are not going to explore.

**Registers** are named `rax`, `rbx`, `rcx`, `rdx`, `rdi`, `rsi`, `rbp`, `rsp`, and `r8`-`r15` for a total of 16 of them. The "letter" ones are named like that for historical reasons: `rax` is "accumulator", `rcx` is "counter", `rdx` is "data" and so on, but, of course, they don't have to be used only for that.

There are also 32-, 16-bit and 8-bit registers that have similar names (`rax` → `eax` → `ax` → `al`). They are not fully separate, but *aliased*: the first 32 bits of `rax` are `eax`, the first 16 bits of `eax` are `ax` and so on. This is made to save die space while maintaining compatibility, and it is also the reason why basic type casts in compiled programming languages are usually free. 

These are just the registers that you use directly in operations. There are also a few special ones that are needed for control flow, as well as a bunch of very wide registers used in vector extensions, but we'll get there in time.

**Memory** addressing is done with `[]` operator, but it can do more than just reinterpret a value stored in a register as a memory location. Address operand takes up to 4 parameters presented in the syntax:

```
SIZE PTR [base + index * scale + displacement]
```

where scale can be 2, 4, or 8, and it calculates the pointer `base + index * scale + displacement` and dereferences it.

This can be useful when you have, say, an array of structures and want to load a specific field of its $i$-th element.

Addressing operator needs to be prefixed with the size:

- `BYTE` for 8 bits
- `WORD` for 16 bits
- `DWORD` for 32 bits
- `QWORD` for 64 bits

There are also more rare `TBYTE` for 80 bits, and `XMMWORD`, `YMMWORD` and `ZMMWORD` for 128, 256 and 512 bits respectively.

(These types don't have to be written in uppercase, but this is how most compilers emit them.)


## Alternative Syntax

There are actually multiple *assemblers* (the programs that produce machine code from assembly) with different assembly languages, but only two x86 syntaxes are widely used. They are commonly called after the two companies that used them and had dominant influence on programming during that era:

- The *AT&T syntax*, used by default by all Linux tools.
- The *Intel syntax*, used by default... by Intel.

These syntaxes are also sometimes called *GAS* and *NASM* respectively, by the names of the two primary assemblers that use them (*GNU Assembler* and *Netwide Assembler*).

We used Intel syntax in this chapter. Here is how the summation loop looks like in AT&T asm:

```asm
loop:
    addl (%rax), %edx
    addq $4, %rax
    cmpq %rcx, %rax
    jne  loop
```

Key differences can be summarized as follows:

1. The *last* operand is used to specify destination.
2. Register names and constants need to be prefixed by `%` and `$` respectively.
3. Memory addressing looks like this: `displacement(%base, %index, scale)`.
4. Both `;` and `#` can be used as comments.

And, most importantly, in AT&T instruction names need to be "suffixed" (`addq`, `movl`, `cmpq`, etc.) to specify what size operands are being manipulated:

- `b` = byte (8 bit)
- `w` = word (16 bit)
- `l` = long (32 bit integer or 64-bit floating point)
- `q` = quad (64 bit)
- `s` = single (32-bit floating point)
- `t` = ten bytes (80-bit floating point)

In Intel syntax this information is inferred from operands (which is why you also need to specify sizes of pointers).

Most tools that produce or consume x86 assembly can do so in both syntaxes, so you can just pick the one you like more and don't worry.
