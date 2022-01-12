---
title: Machine Code Layout
weight: 10
---

Computer engineers like to mentally split the [pipeline of a CPU](/hpc/pipelining) into two parts: the *front-end*, where instructions are fetched from memory and decoded, and the *back-end*, where they are scheduled and finally executed. Typically, the performance is bottlenecked by the execution stage, and for this reason, most of the efforts in this book are going to be spent towards optimizing around the back-end.

But sometimes the reverse can happen, when the front-end doesn't feed instructions to the back-end fast enough to saturate it. This can happen for many reasons, all ultimately having something to do with how the machine code is laid out in memory.

Anecdotal cases when you delete a dead code that were never called anyways and get a performance improvement, and or swap two functions and get a performance deterioration.

### CPU Front-End

Before the machine code gets transformed into instructions, and CPU understands what the programmer wants, it first needs to go through two important stages that we are interested in: *fetch* and *decode*.

During the **fetch** stage, the CPU simply loads a fixed-size chunk of bytes from the main memory, which contains the binary encodings of some number of instructions. This block size is typically 32 bytes on x86, although it may vary on different machines. An important nuance is that this block has to be [aligned](/hpc/cpu-cache/cache-lines): the address of the chunk must be multiple of its size (32B, in our case).

Next comes the **decode** stage: the CPU looks at this chunk of bytes, discards everything that comes before the instruction pointer, and splits the rest of them into instructions. Machine instructions are encoded using a variable amount of bytes: something simple and very common like `inc rax` takes one byte, while some obscure instruction with encoded constants and behavior-modifying prefixes may take up to 15. So, from a 32-byte block, a variable number of instructions may be decoded, but no more than a certain machine-dependant limit called the *decode width*. On my CPU (a [Zen 2](https://en.wikichip.org/wiki/amd/microarchitectures/zen_2)), the decode width is 4, which means that on each cycle, up to 4 instructions can be decoded and passed to the next stage.

The stages work in pipelined fashion: if the CPU can tell (or [predict](/hpc/pipelining/branching/)) which instruction block it needs next, then the fetch stage doesn't wait for the last instruction in the current block to be decoded and loads the next one right away.

### Unequal Branches

When you have. If there is any

This feature also makes the performance of the two branches of an "if" unequal. For example:

```nasm
; if (x < y) swap(x, y);
function:
    cmp  rax, rbx
    js   ok
    xchg rax, rbx
ok:
    ; [function body]
```

```nasm
function:cmp rax, rbx
js ok
neg rax
ok:
    ; [function body]
swap:
    xchg rax, rbx
    jmp  ok
```

You don't have to decode the things you are not going to execute anyway.

You can [hint](/hpc/compilation/situational) the compiler which one you think is going to be more likely.

### Code Alignment

The fact that the instructions blocks have to be aligned is relevant for performance. Image that you need to execute an instruction sequence that starts on the last byte of a 32B-aligned block. You may be able to execute the first instruction without additional delay, but for the subsequent ones, you have to wait one additional cycle to do another instruction fetch. If the code block was aligned on a 32B boundary, then up to 4 instructions could be decoded and then executed concurrently — unless they are extra long or interdependent.

Having this in mind, compilers often do a seemingly harmful optimization: they sometimes prefer instructions with longer machine codes, and even insert dummy instructions that do nothing[^nop] — in order to get key jump locations aligned on a suitable power-of-two boundary.

[^nop]: Such instructions are called no-op, or NOP instructions. On x86, the "official way" of doing nothing is `xchg rax, rax` (swap a register with itself): the CPU recognizes it and doesn't spend extra cycles executing it, except for the decode stage. The `nop` shorthand maps to the same machine code.

In GCC, you can use `-falign-labels=n` flag to specify a particular alignment policy, [replacing](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html) `-labels` with `-function`, `-loops`, or `-jumps` if you want ot be more selective. On `-O2` and `-O3` levels of optimization, it is enabled by default — without setting a particular alignment, in which case it uses a (usually reasonable) machine-dependent default value.

There may be a little waste if you jump to instructions.
This has the same disadvantages: it increases the binary size.

It also has a side effect that you can remove a dead code (a function that wasn't ever used anyway) and the performance goes up.

### Instruction Cache

The same memory as, except that the lower levels of the cache system may be separate, because you wouldn't want read some array value to kick out your instructions.

The second consideration is that.

- This is why huge alignments are .
- Unrolling is only beneficial up to some extent, because.
- Inlining functions is not always optimal, because it reduces code sharing, requiring more instruction cache.

On my Zen 2 CPU, the decode width is 4. 

Decoded Stream Buffer (DSB) and instruciton cache.

LSD

Having to decode a bunch of extra NOPs is usually not a problem.

To improve locality, it makes sense to group hot code with hot code and cold code with cold code.

If you need many parts of the code, you would want to limit your binary size (the reachable part of the program text section, to be more exact) lower than the instruction cache.

Check out Facebook's [Binary Optimization and Layout Tool](https://engineering.fb.com/2018/06/19/data-infrastructure/accelerate-large-scale-applications-with-bolt/)
