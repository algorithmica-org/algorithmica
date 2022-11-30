---
title: Machine Code Layout
weight: 10
published: true
---

Computer engineers like to mentally split the [pipeline of a CPU](/hpc/pipelining) into two parts: the *front-end*, where instructions are fetched from memory and decoded, and the *back-end*, where they are scheduled and finally executed. Typically, the performance is bottlenecked by the execution stage, and for this reason, most of our efforts in this book are going to be spent towards optimizing around the back-end.

But sometimes the reverse can happen when the front-end doesn't feed instructions to the back-end fast enough to saturate it. This can happen for many reasons, all ultimately having something to do with how the machine code is laid out in memory, and affect performance in anecdotal ways, such as removing unused code, swapping "if" branches, or even changing the order of function declarations causing performance to either improve or deteriorate.

### CPU Front-End

Before the machine code gets transformed into instructions, and the CPU understands what the programmer wants, it first needs to go through two important stages that we are interested in: *fetch* and *decode*.

During the **fetch** stage, the CPU simply loads a fixed-size chunk of bytes from the main memory, which contains the binary encodings of some number of instructions. This block size is typically 32 bytes on x86, although it may vary on different machines. An important nuance is that this block has to be [aligned](/hpc/cpu-cache/cache-lines): the address of the chunk must be multiple of its size (32B, in our case).

<!-- todo: what happens when an instruction crosses the boundary? -->

Next comes the **decode** stage: the CPU looks at this chunk of bytes, discards everything that comes before the instruction pointer, and splits the rest of them into instructions. Machine instructions are encoded using a variable number of bytes: something simple and very common like `inc rax` takes one byte, while some obscure instruction with encoded constants and behavior-modifying prefixes may take up to 15. So, from a 32-byte block, a variable number of instructions may be decoded, but no more than a certain machine-dependent limit called the *decode width*. On my CPU (a [Zen 2](https://en.wikichip.org/wiki/amd/microarchitectures/zen_2)), the decode width is 4, which means that on each cycle, up to 4 instructions can be decoded and passed to the next stage.

The stages work in a pipelined fashion: if the CPU can tell (or [predict](/hpc/pipelining/branching/)) which instruction block it needs next, then the fetch stage doesn't wait for the last instruction in the current block to be decoded and loads the next one right away.

<!--

Decoded Stream Buffer (DSB)

Loop Stream Detector (LSD)

-->

### Code Alignment

Other things being equal, compilers typically prefer instructions with shorter machine code, because this way more instructions can fit in a single 32B fetch block, and also because it reduces the size of the binary. But sometimes the reverse is prefereable, due to the fact that the fetched instructions' blocks must be aligned.

Imagine that you need to execute an instruction sequence that starts on the last byte of a 32B-aligned block. You may be able to execute the first instruction without additional delay, but for the subsequent ones, you have to wait for one additional cycle to do another instruction fetch. If the code block was aligned on a 32B boundary, then up to 4 instructions could be decoded and then executed concurrently (unless they are extra long or interdependent).

Having this in mind, compilers often do a seemingly harmful optimization: they sometimes prefer instructions with longer machine codes, and even insert dummy instructions that do nothing[^nop] in order to get key jump locations aligned on a suitable power-of-two boundary.

[^nop]: Such instructions are called no-op, or NOP instructions. On x86, the "official way" of doing nothing is `xchg rax, rax` (swap a register with itself): the CPU recognizes it and doesn't spend extra cycles executing it, except for the decode stage. The `nop` shorthand maps to the same machine code.

In GCC, you can use `-falign-labels=n` flag to specify a particular alignment policy, [replacing](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html) `-labels` with `-function`, `-loops`, or `-jumps` if you want to be more selective. On `-O2` and `-O3` levels of optimization, it is enabled by default — without setting a particular alignment, in which case it uses a (usually reasonable) machine-dependent default value.

<!-- Having to decode a bunch of extra NOPs is usually not a problem. -->

### Instruction Cache

The instructions are stored and fetched using largely the same [memory system](/hpc/cpu-cache) as for the data, except maybe the lower layers of cache are replaced with a separate *instruction cache* (because you wouldn't want a random data read to kick out the code that processes it).

The instruction cache is crucial in situations when you either:

- don't know what instructions you are going to execute next, and need to fetch the next block with [low latency](/hpc/cpu-cache/latency),
- or are executing a long sequence of verbose-but-quick-to-process instructions, and need [high bandwidth](/hpc/cpu-cache/bandwidth).

The memory system can therefore become the bottleneck for programs with large machine code. This consideration limits the applicability of the optimization techniques we've previously discussed:

- [Inlining functions](../functions) is not always optimal, because it reduces code sharing and increases the binary size, requiring more instruction cache.
- [Unrolling loops](../loops) is only beneficial up to some extent, even if the number of iterations is known during compile time: at some point, the CPU would have to fetch both instructions and data from the main memory, in which case it will likely be bottlenecked by the memory bandwidth.
- Huge [code alignments](#code-alignment) increase the binary size, again requiring more instruction cache. Spending one more cycle on fetch is a minor penalty compared to missing the cache and waiting for the instructions to be fetched from the main memory.

Another aspect is that placing frequently used instruction sequences on the same [cache lines](/hpc/cpu-cache/cache-lines) and [memory pages](/hpc/cpu-cache/paging) improves [cache locality](/hpc/external-memory/locality). To improve instruction cache utilization, you should  group hot code with hot code and cold code with cold code, and remove dead (unused) code if possible. If you want to explore this idea further, check out Facebook's [Binary Optimization and Layout Tool](https://engineering.fb.com/2018/06/19/data-infrastructure/accelerate-large-scale-applications-with-bolt/), which was recently [merged](https://github.com/llvm/llvm-project/commit/4c106cfdf7cf7eec861ad3983a3dd9a9e8f3a8ae) into LLVM.

### Unequal Branches

Suppose that for some reason you need a helper function that calculates the length of an integer interval. It takes two arguments, $x$ and $y$, but for convenience, it may correspond to either $[x, y]$ or $[y, x]$, depending on which one is non-empty. In plain C, you would probably write something like this:

```c++
int length(int x, int y) {
    if (x > y)
        return x - y;
    else
        return y - x;
}
```

In x86 assembly, there is a lot more variability to how you can implement it, noticeably impacting performance. Let's start with trying to map this code directly into assembly:

```nasm
length:
    cmp  edi, esi
    jle  less
    ; x > y
    sub  edi, esi
    mov  eax, edi
done:
    ret
less:
    ; x <= y
    sub  esi, edi
    mov  eax, esi
    jmp  done
```

While the initial C code seems very symmetrical, the assembly version isn't. This results in an interesting quirk that one branch can be executed slightly faster than the other: if `x > y`, then the CPU can just execute the 5 instructions between `cmp` and `ret`, which, if the function is aligned, are all going to be fetched in one go; while in case of `x <= y`, two more jumps are required.

It may be reasonable to assume that the `x > y` case is *unlikely* (why would anyone calculate the length of an inverted interval?), more like an exception that mostly never happens. We can detect this case, and simply swap `x` and `y`:

```c++
int length(int x, int y) {
    if (x > y)
        swap(x, y);
    return y - x;
}
```

The assembly would go like this, as it typically does for the if-without-else patterns:

```nasm
length:
    cmp  edi, esi
    jle  normal     ; if x <= y, no swap is needed, and we can skip the xchg
    xchg edi, esi
normal:
    sub  esi, edi
    mov  eax, esi
    ret
```

The total instruction length is 6 now, down from 8. But it is still not quite optimized for our assumed case: if we think that `x > y` never happens, then we are wasteful when loading the `xchg edi, esi` instruction that is never going to be executed. We can solve this by moving it outside the normal execution path:

```nasm
length:
    cmp  edi, esi
    jg   swap
normal:
    sub  esi, edi
    mov  eax, esi
    ret
swap:
    xchg edi, esi
    jmp normal
```

This technique is quite handy when handling exceptions cases in general, and in high-level code, you can give the compiler a [hint](/hpc/compilation/situational) that a certain branch is more likely than the other:

```c++
int length(int x, int y) {
    if (x > y) [[unlikely]]
        swap(x, y);
    return y - x;
}
```

This optimization is only beneficial when you know that a branch is very rarely taken. When this is not the case, there are [other aspects](/hpc/pipelining/hazards) more important than the code layout, that compel compilers to avoid any branching at all — in this case by replacing it with a special "conditional move" instruction, roughly corresponding to the ternary expression `(x > y ? y - x : x - y)` or calling `abs(x - y)`:

```nasm
length:
    mov   edx, edi
    mov   eax, esi
    sub   edx, esi
    sub   eax, edi
    cmp   edi, esi
    cmovg eax, edx  ; "mov if edi > esi"
    ret
```

Eliminating branches is an important topic, and we will spend [much of the next chapter](/hpc/pipelining/branching) discussing it in more detail.

<!--

This architecture peculiarity

When you have branches in your code, there is a variability in how you can place their instruction sequences in the memory — and surprisingly, .

```nasm
length:
    mov   edx, edi
    mov   eax, esi
    sub   edx, esi
    sub   eax, edi
    cmp   edi, esi
    cmovg eax, edx  ; "mov if edi > esi"
    ret
```

Granted that `x > y` never or almost never happens, the branchy variant will be 2 instructions shorter.

https://godbolt.org/z/bb3a3ahdE

(The compiler can't optimize it because it's technically [not allowed to](/hpc/compilation/contracts): despite `y - x` being valid, `x - y` could over/underflow, causing undefined behavior. Although fully correct, I guess the compiler just doesn't date executing it.)

We will spend [much of the next chapter](/hpc/pipelining/branching) discussing it in more detail.

You don't have to decode the things you are not going to execute anyway.

In general, you want to, and put rarely executed code away — even in the case of if-without-else patterns.

-->
