---
title: Computer Architecture & Assembly
weight: 1
---

As software engineers, we absolutely love building and using abstractions.

Just imagine how much stuff happens when you load a URL. You type something on a keyboard, key presses are somehow detected by the OS and get sent to the browser, browser parses the URL and asks the OS to make a network request, then comes DNS, routing, TCP, HTTP and all the other OSI layers, browser parses HTML, JavaScript works its magic, some representation of a page gets sent over to GPU for rendering, image frames get sent to the monitor... and each of these steps probably involves doing dozens of more specific things on the inside.

Abstractions help us in reducing all this complexity down to a single *interface* that describes what a certain module can do without fixing a concrete implementation. This provides double benefits: engineers working on a higher-level modules only need to know the (much smaller) interface, and engineers working on the module itself get freedom to optimize and refactor the implementation as long as it complies with its contracts.

Hardware engineers love abstractions too. An abstraction of a CPU is called an *instruction set architecture* (ISA), and it defines how a computer should work from a programmer's perspective. Similarly to software interfaces, it gives computer engineers the ability to improve on existing CPU designs while also giving its users — us, programmers — the confidence that things that worked before won't break on newer chips.

The ISA is essentially a low-level machine language definition that defines how the hardware will interpret the machine language. Apart from instructions and their binary encodings, ISAs define supported data types, numbers, sizes and purposes of registers, memory model and input/output model. And similarly to software interfaces, ISAs can be extended too: in fact, they are often updated, mostly in a backwards-compatible way, and add new and more specialized instructions that improve performance.

Tell about javascript division in arm?

## RISC vs CISC

Historically, there has been many competing ISAs in use. But unlike [character encodings and instant messaging protocols](https://xkcd.com/927/), developing and maintaining a completely separate ISA is costly, so CPUs ended up converging to one of the two families:

- arm chips, which are used in almost all mobile devices, as well as other computer-like devices such as TVs, smart fridges, microwaves, [car autopilots](https://en.wikipedia.org/wiki/Tesla_Autopilot) and so on. They are designed by a British company of the same name, as well as a number of electronics manufacturers including Apple and Samsung.
- x86 chips, which are used in almost all servers and desktops with a few notable exceptions such as Apple's M1 MacBooks and the current world's fastest supercomputer Fugaku, both of which use arm-based CPUs. They are designed by a duopoly of Intel and AMD.

Modern 64-bit version of x86 is known as AMD64, Intel 64, or more vendor-neutral x86-64 or x64. A similar 64-bit extension of arm is called AArch64 or ARM64. We will just use plain "x86" and "arm" implying the 64-bit versions.

The main difference between them is that of architectural complexity, which is more of a design philosophy rather than some strictly defined property.

- arm CPUs are *reduced* instruction set computers (RISC). They improve performance by keeping the instruction set small and highly optimized, alhtough less common operations have to be implemented with subroutines involving several instructions.
- x86 CPUs are *complex* instruction set computers (CISC). They go about improving performacne by adding many specialized instructions, some of which may only be rarely used in practical programs.

The main advantages of RISC designs are manufacturing cost and power usage, so it's not surprising that the market segmented itself with arm dominating battery-powered, general-purpose devices and leaving neural network and galois field calculations to server-grade, highly-specialized x86s.

## Assembly Language

Please don't get scared away: it's not that complicated.

Machine language is just a stream of instructions encoded with variable amount of bytes that specify the instruction number (called opcode), what its operands are, and where to store the result.

A much more human friendly rendition of machine language, called assembly language, uses mnemonic codes to refer to machine code instructions and symbolic names to refer to registers and other storage locations.

Jumping right into it, here is how you add two numbers (`*c = *a + *b`) in arm assembly:

```asm
# *a = x0, *b = x2, *c = x2
ldr w0, [x0]    # load 4 bytes from wherever x0 points into w0
ldr w1, [x1]    # load 4 bytes from wherever x1 points into w1
add w0, w0, w1  # add w0 with w1 and save the result to w0
str w0, [x2]    # write contents of w0 to wherever x2 points/
```

Here is the same operation in x86 assembly:

```asm
# *a = rsi, *b = rdi, *c = rdx 
movl (%rsi), %eax  # load 4 bytes from wherever rsi points into eax
addl (%rdi), %eax  # add whatever is stored at rdi to eax
movl %eax, (%rdx)  # write contents of eax to wherever rdx points
```

There are a few more features in the language — you can observe that "#" is be used for comments and []/() are referring to memory locations — but apart from that, assembly is a very minimal language. It reflects the machine language as closely as possible, up to the point where there is almost 1:1 correspondence between machine code and assembly, so that you can, in fact, turn any compiled program back into its assembly form by a process called disassembly — although everything non essential like comments will not be preserved.

Note that the two snippets above are not just syntactically different. Both are optimized codes produced by a compiler, but arm version uses 4 instruction, while x86 version uses 3. The `addl (%rdi), %eax` instruction is what's called *fused instruction* that does a load and an add in one go, and it is one of the perks that CISC can provide.

Since there are far more differences between the architectures, from here on and until the rest of the book we will only provide examples for x86, which is probably what most readers will optimize for, although many of the introduced concepts will be architecture-agnostic.

## Instruction and Registers

Due to historic reasons, instruction mnemonics in most assembly languages are very terse. Back when people used to write assembly by hand and repeatedly wrote the same set of common instructions, one less character to type was one step away from insanity.

Operations names are usually comprised of a "base name" and optional one-letter suffixes that determine what size operands are being manipulated:

- `b` = byte (8 bit)
- `w` = word (16 bit)
- `l` = long (32 bit integer or 64-bit floating point)
- `q` = quad (64 bit)
- `s` = single (32-bit floating point)
- `t` = ten bytes (80-bit floating point)

For example, `movl` is "move a long word", `inc` is "increment by 1" and `idiv` is "signed division". You can look up the description of an instruction by its name in [one of x86 references](https://www.felixcloutier.com/x86/), but most instructions do what you'd think they do.

Most instructions write their result into the last operand, which can also be involved in the computation like in the `addl (%rdi), %eax` example we saw before. Operands can be either constant values, registers or memory locations.

**Constants** are just numbers prefixed with `$` sign: `$42`, `$0x2a`. They are embedded right into the machine code.

**Registers** are prefixed with `%` sign. There are 16 of them, named %rax, %rbx, %rcx, %rdx, %rdi, %rsi, %rbp, %rsp, and %r8-r15. The "letter" ones are named like that for historical reasons: `rax` is "accumulator", `rcx` is "counter", `rdx` is "data" and so on, but, of course, they don't have to be used only for that.

There are also 32-, 16-bit and 8-bit registers that have similar names (`rax` → `eax` → `ax` → `al`, but they are not fully separate but *aliased*: the first 32 bits of `rax` are `eax`, the first 16 bits of `eax` are `ax` and so on. This is made to save die space while maintaining compatibility, and it is also the reason why basic type casts in high(er)-level languages are free. 

These are just the registers that you use directly in operations. There are also a few special ones that are needed for control flow, as well as a bunch of very wide registers used in vector extensions, but we'll get there in time.

**Memory** addressing is done with `()` operator, but it can do more than just reinterpret a value stored in a register as a memory location.

Address operand takes up to 4 parameters presented in syntax `displacement(%base, %index, scale)`, where scale can be 2, 4, or 8, and calculates `$base + %index * scale + displacement`. This can be useful when you have, say, an array of structures and want to load a specific field of its $i$-th element.

## Control Flow

Let's consider a slightly more complex example:

```asm
LOOP:
    addl (%rax), %edx
    addq $4, %rax
    cmpq %rcx, %rax
    jne  LOOP
```

It calculates the sum of a 32-bit integer array, just as a simple `for` loop would.

The "body" of the loop is `addl (%rax), %edx`. This instruction loads data from the iterator, `rax` (we are on a 64-bit system, so all pointers are 64-bit), and adds it to the accumulator, `edx`.

Next, we move the iterator 4 bytes forward with `addq $4, %rax`.

Then a complicated thing happens. Assembly doesn't have if-s, for-s, functions or other control flow structures that high level languages have. What it does have is `goto`, or "jump", how it is known in low-level programming.

Jump "jumps" to location specified by a label, which needs to be declared somewhere else as a string followed by `:`. When converted to machine code, it is replaced by an instruction that moves the instruction pointer by a fixed number of bytes so that it ends up at the instruction pointed by the label. Label can be any string, but compilers don't get creative with naming and just use either `.Ln` pattern for loops, where `n` is the line number in the source, and function names and their signatures when picking names for labels.

*Unconditional* jump (`jmp`) can only be used to implement `while (true)` kind of loops or stitch programs together. A family of *conditional* jumps is used to implement actual control flow.

It is reasonable to think that these conditions are computed as `bool`-s somewhere and passed to conditional jumps as operands — after all, this is how it works in programming languages — but that's not how it's implemented in hardware. Conditional operations use a special `FLAGS` register, which is populated by executing certain instructions that perform some kind of checks.

In our example, `cmpq %rcx, %rax` compares the iterator, `rax`, with the end-of-array pointer, `rcx`. This updates the flags register, and now it can be used by `jne LOOP`, which looks up a certain bit there that tells whether the two values are equal or not, and then either jumps back to the beginning or breaks the loop.

### Loop Unrolling

One thing you might noticed about the loop above is that there is a lot of overhead to processing a single element. There is just one useful instruction executed during each cycle, and the other 3 are either incrementing the iterator or trying to find out if we are done yet.

What we can do here is to *unroll* the loop by grouping iterations together — like writing something like this in C:

```c++
for (int i = 0; i < n; i += 4) {
    s += a[i];
    s += a[i + 1];
    s += a[i + 2];
    s += a[i + 3];
}
```

Back to assembly, it will look like this:

```asm
LOOP:
    addl (%rax), %edx
    addl 4(%rax), %edx
    addl 8(%rax), %edx
    addl 12(%rax), %edx
    addq $16, %rax
    cmpq %rsi, %rax
    jne  LOOP
```

Now we only need 3 loop control instructions for 4 useful ones, and this can be continued to reduce the overhead almost to zero.

In practice though, unrolling loops isn't always necessary for performance because of a mechanism called *out-of-order execution*. Modern processors don't actually execute instructions one-by-one, but maintain a "pool" of pending instructions so that two independent operations can be executed at the same without waiting for each other to finish. High-end CPUs can run up to 6 instructions on the same cycle this way, although practical programs rarely average more than 2-3 instructions per cycle.

This is our case too: the real speedup from unrolling won't be fourfold, because incrementing the counter and checking for end-of-loop are independent from the loop body, and can be sheduled to run concurrently with it.

Light bulb: independent instructions can be executed concurrently by CPU

### Branch Prediction

The way this mechanism works is that it loads a few instructions ahead of time. The downside is that if we can't determine what is going to be loaded (if we can't predict which branch a jump is going to take).

By default it takes the branch that goes directly after jump, but then it starts using statistics. They aren't very smart, but can detect simple patterns.

Jumps aren't the only instructions that use flags. Another example are the `cmov` ("conditional move") instructions that return one of two values based on a condition, so that when you write simple things like `c = (cond ? a : b)` compiler emits a single instruction instead of an expensive jump with two branches.

It actually matters a lot.

Light bulb: branch prediction is expensive

## Functions

To call a function, you need to jump to its beginning and then jump back. But then two important problems arise:

1. What if we store data in the same registers that the callee does?
2. Where is "back"?

Both of these concerns can be solved by having a dedicated location in memory where we write all the information we need to return from the function before calling it. This location is called *the stack*.

The stack works the same way all software stacks do, and similarly implemented as just two pointers:

- The *base pointer* that marks the start of the stack and is conventionally stored in `rbp`.
- The *stack pointer* that marks the last element on the stack and is conventionally stored in `rsp`.

When you need to call a function, you can push all your local variables onto the stack (which you can also do it in other circumstances, e. g. when you run out of registers), push the instruction pointer as well, and make the jump. When exiting from a function, you look at the pointer stored on top of the stack, jump there, and then carefully read all the variables stored on the stack back into their registers.

You can implement all that with the usual memory operations and jumps, but because of how frequently it is used, there are 4 special instructions for doing this — you would call then syntactic sugar if it wasn't how it's actually implemented in hardware:

- `push` writes data to stack pointer and increments it.
- `pop` reads data from stack pointer and decrements it.
- `call` puts the address of the following instruction on top of stack and jumps to a label.
- `ret` reads the return address from the top of the stack and jumps to it.

Over time, people who develop compilers and operating systens came up with conventions to how to call functions. This allows splitting compilation into separate units, and to re-use already compiled libraries, as well as writing them in different programming langauges. This is called shared library and linking. Of course, you don't have to follow these conventions in local functions.

There are a lot more [conventions](https://en.wikipedia.org/wiki/X86_calling_conventions) and nuances, but we won't go in detail here, because this book is about performance, and the best way to deal with functions calls is actually to avoid them.

### Overhead of Recursion

Packing and unpacking data to and from the stack can create a huge overhead for smaller functions, so, when possible, optimizing compilers will *inline* them by stitching their code into the caller and resolving conflicts over registers. This is straighforward when the function doesn't make any other function calls, or at least if these calls are not recursive.

If the function is recursive, it is still often possible to make it "call-less" by restructuring it. This is the case when the function is *tail recursive*, that is, it returns right after making a recursive call. Since no actions are required after the call, there is also no need for storing anything on the stack, and a recursive call can be safely replaced with a jump to the beginning, effectively turning the function into a loop.

Light bulb: The primary reason why recursion can be slow is because it stores data on stack, which need to be stored and loaded from memory, while iterative and "tail recursive" algorithms don't.

## Alternative Syntax

There are actually multiple assemblers (that is, the programs that produce machine code from assembly) with drastically different assembly languages, but only two x86 syntaxes are widely used. They are commonly called after the two companies that used them and had dominant influence on programming during that era:

- The *AT&T syntax*, used by default by all Unix and Linux tools
- The *Intel syntax*, used by default... by Intel

We used the AT&T syntax in this chapter. Here is how the summation loop looks like in Intel asm:

```asm
LOOP:
    add edx, DWORD PTR [rax]
    add rax, 4
    cmp rax, rcx
    jne LOOP
```

Key differences can be summarized as follows:

1. The first operand is used as destination.
2. Register names and constants don't need to be prefixed by `%` or `$`.
3. Memory addressing looks like `[base + reg + reg * scale + displacement]`.
4. Instructions are not suffixed, type information is inferred from operands (which looks somewhat awkward for pointers)
5. Only `;` is used for comments (while AT&T allows both `;` and `#`)

Most tools that produce or consume x86 assembly can do so in both syntaxes, so you can just pick the one you like more and don't worry.

---

AT&T immediate operands use a $ to denote them, whereas Intel immediate operands are undelimited. Thus, when referencing the decimal value 4 in AT&T syntax, you would use dollar 4, and in Intel syntax you would just use 4.
AT&T prefaces register names with a %, while Intel does not. Thus, referencing the EAX register in AT&T syntax, you would use %eax.
AT&T syntax uses the opposite order for source and destination operands. To move the decimal value 4 to the EAX register, AT&T syntax would be movl $4, %eax, whereas for Intel it would be mov eax, 4.
AT&T syntax uses a separate character at the end of mnemonics to reference the data size used in the operation, whereas in Intel syntax the size is declared as a separate operand. The AT&T instruction movl $test, %eax is equivalent to mov eax, dword ptr test in Intel syntax.
Long calls and jumps use a different syntax to define the segment and offset values. AT&T syn- tax uses ljmp 
s
e
c
t
i
o
n
,
offset, whereas Intel syntax uses jmp section:offset.

## Assembly Idioms

Lastly, there are a few "WTF is this" idioms in assembly language which felt wrong not to include in this chapter:

- The `lea` ("load effective address") instruction performs memory addressing and stores the address itself in a register without doing any memory operations. While its intended usage if to get addresses of class fields, it is often used as a trick that would otherwise involve 1 multiplication and 2 additions. For example, you can multiply by 3, 5 and 9 with it.

- `test %rax, %rax` is the optimal way to check if a value is zero. `test` instruction "and"-s two values and tests flags according to result. You can use `cmp %rax, $0`, but it's machine code is one byte longer. (And yes, this also implies that checking if a signed value is exactly zero is faster than checking if it is larger than zero???)

- Likewise, `xor %rax, %rax` is the fastest way to set a register to zero.

- `xchg %rax, %rax` swaps a register with itself, and it is the official way to do nothing: `nop` maps to the same machine code. You may want insert these operations to pad other instructions to specific addresses for a better memory layout.

If you think that this is hacky and should be simplified, just remember that one level of abstraction away there's literally a rock that we tricked into thinking.
