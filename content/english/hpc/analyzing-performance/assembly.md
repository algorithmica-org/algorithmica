---
title: Computer Architecture & Assembly
weight: 1
---

One huge mistake I made when I was learning how to write faster programs was to rely solely on the empirical approach. Not understanding how things really worked, I would semi-randomly swap nested loops, rearrange arithmetic, combine branch conditions or inline functions by hand, hoping for improvement.

Sadly, this is how an overwhelming majority of people approach optimization. Most texts about performance do not teach you to reason about performance qualitatively, but rather give you general advice about certain implementation approaches.

It would have probably saved me dozens, if not hundreds of hours if I learned computer architecture before doing algorithmic programming. So even if most people may not like it, we are going to start with the unpopular topic: reading assembly.

## Instruction Set Architectures

As software engineers, we absolutely love building and using abstractions.

Just imagine how much stuff happens when you load a URL. You type something on a keyboard; key presses are somehow detected by the OS and get sent to the browser; browser parses the URL and asks the OS to make a network request; then comes DNS, routing, TCP, HTTP and all the other OSI layers; browser parses HTML and JavaScript works its magic; some representation of a page gets sent over to GPU for rendering; image frames get sent to the monitor… and each of these steps probably involves doing dozens of more specific things in the process.

Abstractions help us in reducing all this complexity down to a single *interface* that describes what a certain module can do without fixing a concrete implementation. This provides double benefits:

- engineers working on higher-level modules only need to know the (much smaller) interface,
- engineers working on the module itself get freedom to optimize and refactor the implementation as long as it complies with its *contracts*.

Hardware engineers love abstractions too. An abstraction of a CPU is called an *instruction set architecture* (ISA), and it defines how a computer should work from a programmer's perspective. Similarly to software interfaces, it gives computer engineers the ability to improve on existing CPU designs while also giving its users — us, programmers — the confidence that things that worked before won't break on newer chips.

The ISA essentially defines how the hardware should interpret the machine language. Apart from instructions and their binary encodings, ISA importantly defines counts, sizes and purposes of registers, memory model and input/output model. Similarly to software interfaces, ISAs can be extended too: in fact, they are often updated, mostly in a backwards-compatible way, to add new and more specialized instructions that can improve performance.

### RISC vs CISC

Historically, there has been many competing ISAs in use. But unlike [character encodings and instant messaging protocols](https://xkcd.com/927/), developing and maintaining a completely separate ISA is costly, so mainstream CPUs ended up converging to one of the two families:

- **arm** chips, which are used in almost all mobile devices, as well as other computer-like devices such as TVs, smart fridges, microwaves, [car autopilots](https://en.wikipedia.org/wiki/Tesla_Autopilot) and so on. They are designed by a British company of the same name, as well as a number of electronics manufacturers including Apple and Samsung.
- **x86**[^x86] chips, which are used in almost all servers and desktops, with a few notable exceptions such as Apple's M1 MacBooks and the current [world's fastest supercomputer](https://en.wikipedia.org/wiki/Fugaku_(supercomputer)), both of which use arm-based CPUs. They are designed by a duopoly of Intel and AMD.

[^x86]: Modern 64-bit versions of x86 are known as "AMD64", "Intel 64", or by the more vendor-neutral names of "x86-64" or just "x64". A similar 64-bit extension of arm is called "AArch64" or "ARM64". In this book we will just use plain "x86" and "arm" implying the 64-bit versions.

The main difference between them is that of architectural complexity, which is more of a design philosophy rather than some strictly defined property:

- arm CPUs are *reduced* instruction set computers (RISC). They improve performance by keeping the instruction set small and highly optimized, although some less common operations have to be implemented with subroutines involving several instructions.
- x86 CPUs are *complex* instruction set computers (CISC). They improve performance by adding many specialized instructions, some of which may only be rarely used in practical programs.

The main advantages of RISC designs are manufacturing cost and power usage, so it's not surprising that the market segmented itself with arm dominating battery-powered, general-purpose devices and leaving the complex neural network and Galois field calculations to server-grade, highly-specialized x86s.

## Assembly Language

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
- The `[reg]` syntaxis is used for "dereferencing" a pointer stored in a register, and on x86 you need to prefix it with size information (`DWORD` here means 32 bit).
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

There are also 32-, 16-bit and 8-bit registers that have similar names (`rax` → `eax` → `ax` → `al`). They are not fully separate, but *aliased*: the first 32 bits of `rax` are `eax`, the first 16 bits of `eax` are `ax` and so on. This is made to save die space while maintaining compatibility, and it is also the reason why basic type casts in compiled programming languages are ususally free. 

These are just the registers that you use directly in operations. There are also a few special ones that are needed for control flow, as well as a bunch of very wide registers used in vector extensions, but we'll get there in time.

**Memory** addressing is done with `[]` operator, but it can do more than just reinterpret a value stored in a register as a memory location. Address operand takes up to 4 paramenters presented in the syntax:

```
SIZE PTR [base + index * scale + displacement]
```

where scale can be 2, 4, or 8, and it calculates the pointer `base + index * scale + displacement` and dereferences it.

This can be useful when you have, say, an array of structures and want to load a specific field of its $i$-th element.

Addressing operator neds to be prefixed with the size:

- `BYTE` for 8 bits
- `WORD` for 16 bits
- `DWORD` for 32 bits
- `QWORD` for 64 bits

There are also more rare `TBYTE` for 80 bits, and `XMMWORD`, `YMMWORD` and `ZMMWORD` for 128, 256 and 512 bits respectively.

(These types don't have to be written in uppercase, but this is how most compilers emit them.)

## Control Flow

Let's consider a slightly more complex example:

```nasm
loop:
    add  edx, DWORD PTR [rax]
    add  rax, 4
    cmp  rax, rcx
    jne  loop
```

It calculates the sum of a 32-bit integer array, just as a simple `for` loop would.

The "body" of the loop is `add edx, DWORD PTR [rax]`. This instruction loads data from the iterator `rax` and adds it to the accumulator `edx`.

Next, we move the iterator 4 bytes forward with `add rax, 4`.

Then a slightly more complicated thing happens. Assembly doesn't have if-s, for-s, functions or other control flow structures that high level languages have. What it does have is `goto`, or "jump", how it is known in the world of low-level programming.

**Jump** "jumps" to location specified by a label, which needs to be declared somewhere else as a string followed by `:`. When converted to machine code, it is replaced by an instruction that moves the instruction pointer by a fixed number of bytes so that it ends up at the instruction pointed by the label.

Label can be any string, but compilers don't get creative with naming and [just use](https://godbolt.org/z/T45x8GKa5) the `.Ln` pattern for loops, where `n` is the line number in the source, and function names with their signatures when picking names for labels.

**Unconditional** jump `jmp` can only be used to implement `while (true)` kind of loops or stitch parts of a program together. A family of **conditional** jumps is used to implement actual control flow.

It is reasonable to think that these conditions are computed as `bool`-s somewhere and passed to conditional jumps as operands: after all, this is how it works in programming languages. But that is not how it is implemented in hardware. Conditional operations use a special `FLAGS` register, which first needs to be populated by executing certain instructions that perform some kind of checks.

In our example, `cmp rax, rcx` compares the iterator `rax` with the end-of-array pointer `rcx`. This updates the flags register, and now it can be used by `jne loop`, which looks up a certain bit there that tells whether the two values are equal or not, and then either jumps back to the beginning or continues to the next instruction, thus breaking the loop.

### Loop Unrolling

One thing you might have noticed about the loop above is that there is a lot of overhead to process a single element. During each cycle, there is only one useful instruction executed, and the other 3 are maintaining the iterator and trying to find out if we are done yet.

What we can do is to *unroll* the loop by grouping iterations together — equivalent to writing something like this in C:

```c++
for (int i = 0; i < n; i += 4) {
    s += a[i];
    s += a[i + 1];
    s += a[i + 2];
    s += a[i + 3];
}
```

In assembly, it would look something like this:

```nasm
loop:
    add  edx, [rax]
    add  edx, [rax+4]
    add  edx, [rax+8]
    add  edx, [rax+12]
    add  rax, 16
    cmp  rax, rsi
    jne  loop
```

Now we only need 3 loop control instructions for 4 useful ones (improvement from $\frac{1}{4}$ to $\frac{4}{7}$ in terms of efficiency), and this can be continued to reduce the overhead almost to zero.

In practice though, unrolling loops isn't always necessary for performance because of a mechanism called *out-of-order execution*. Modern processors don't actually execute instructions one-by-one, but maintain a "pool" of pending instructions so that two independent operations can be executed concurrently without waiting for each other to finish.

This is our case too: the real speedup from unrolling won't be fourfold, because incrementing the counter and checking for end of loop are independent from the loop body and can be sheduled to run concurrently with it.

### Branch Prediction

One more important thing to note is that conditional jumps may be very expensive. This is due to the fact that a modern CPU has a pretty deep "pipeline" or instructions on different stages of execution: some may be just loading from memory, some may be decoding, executing or writing the results. The whole process takes 12-15 cycles, not counting the latency of the operation itself, and you essentially "pay" these 12-15 cycles if you can't predict the next instruction you will be executing well in advance.

For example, consider the following loop that sums all odd numbers in an array:


```cpp
for (int i = 0; i < n; i++)
    if (a[i] & 1)
        s += a[i];
```

It can be implemented like this:

```nasm
loop:
    mov edx, DWORD PTR [rdi]
    mov ecx, edx  ; copy edx=a[i] into temporary register
    and ecx, 1    ; binary "and", and also sets ZF flag if the result is zero
    jne even      ; skip add if a[i] is even
    add eax, edx
even:
    add     rdi, 4
    cmp     rdi, rsi
    jne     loop
```

Modern CPUs are smart: they try to predict which branch is going to be taken. By default, the "don't jump" branch is always assumed, but during execution they keep statistics about branches taken on each instruction, and after a while and they start to predict them by recognizing common patterns.

This works well if the branch is predictable: for example, if all numbers in `a` are even or if 99% of the numbers are odd. This reduces the cost of a branch to almost zero, except for the check itself.

But if the parity of numbers in `a` is completely random, branch prediction will be wrong 50% of the time. Luckily, in simple cases like this, we can remove explicit branching completely by using a special `cmov` ("conditional move") instruction that assigns a value based on a condition:

```nasm
loop:
    mov     edx, DWORD PTR [rdi]
    add     ecx, rax, rdx  ; calculate sum in advance
    and     edx, 1
    cmovne  eax, ecx       ; execute assignment if a[i] is odd
    add     rdi, 4
    cmp     rdi, rsi
    jne     loop
```

This is roughly equivalent to:

```cpp
for (int i = 0; i < n; i++)
    s = (a[i] & 1 ? s + a[i]: s);
```

Branchless computing tricks like this one are especially important in all sorts of parallel algorithms.

## Functions

To call a "function" in assembly, you need to jump to its beginning and then jump back. But then two important problems arise:

1. What if the caller stores data in the same registers as the callee?
2. Where is "back"?

Both of these concerns can be solved by having a dedicated location in memory where we write all the information we need to return from the function before calling it. This location is called *the stack*.

The stack works the same way all software stacks do, and similarly implemented as just two pointers:

- The *base pointer* that marks the start of the stack and is conventionally stored in `rbp`.
- The *stack pointer* that marks the last element on the stack and is conventionally stored in `rsp`.

When you need to call a function, you can push all your local variables onto the stack (which you can also do in other circumstances, e. g. when you run out of registers), push the current instruction pointer as well, and make the jump. When exiting from a function, you look at the pointer stored on top of the stack, jump there, and then carefully read all the variables stored on the stack back into their registers.

You can implement all that with the usual memory operations and jumps, but because of how frequently it is used, there are 4 special instructions for doing this — you would call them "syntactic sugar" if it wasn't how they are actually implemented in hardware:

- `push` writes data to stack pointer and increments it.
- `pop` reads data from stack pointer and decrements it.
- `call` puts the address of the following instruction on top of stack and jumps to a label.
- `ret` reads the return address from the top of the stack and jumps to it.

For example, consider recursive computation of a factorial:

```cpp
int factorial(int n) {
    if (n == 0)
        return 1;
    return factorial(n - 1) * n;
}
```

Equivalent assembly:

```nasm
; convention: return factorial of ebx in eax
factorial:
    test ebx, ebx   ; test if value if zero
    jne  nonzero
    mov  eax, 1     ; return 1
    ret
nonzero:
    push ebx        ; save n to use later in multiplication
    sub  ebx, 1
    call factorial  ; call f(n - 1)
    pop  ebx
    imul eax, ebx
    ret
```

Over time, people who develop compilers and operating systens came up with [conventions](https://en.wikipedia.org/wiki/X86_calling_conventions) on how to call functions. These conventions allow software engineering marvels such as splitting compilation into separate units, re-using already compiled libraries and even writing them in different programming langauges. Of course, you don't have to follow these conventions in local functions.

There are a lot more nuances, but we won't go in detail here, because this book is about performance, and the best way to deal with functions calls is actually to avoid making them in the first place.

### Overhead of Recursion

Moving data to and from the stack creates a huge overhead for smaller functions. When possible, optimizing compilers will *inline* function calls by stitching callee's code into the caller and resolving conflicts over registers. This is straighforward to do when callee doesn't make any other function calls, or at least if these calls are not recursive.

If the function is recursive, it is still often possible to make it "call-less" by restructuring it. This is the case when the function is *tail recursive*, that is, it returns right after making a recursive call. Since no actions are required after the call, there is also no need for storing anything on the stack, and a recursive call can be safely replaced with a jump to the beginning, effectively turning the function into a loop.

To make our `factorial` function tail recursive, we can pass a "current product" argument to it:

```cpp
int factorial(int n, int p = 1) {
    if (n == 0)
        return 1;
    return factorial(n - 1, p * n);
}
```

Then this function can be easily unrolled as a loop:

```nasm
; assuming n > 0
factorial:
    mov  eax, 1
loop:
    imul eax, ebx
    sub  ebx, 1
    jne  loop
    ret
```

To summarize: the primary reason why recursion can be slow is because it needs to read and write data to the stack, while iterative and "tail recursive" algorithms do not.

## Alternative Syntax

There are actually multiple *assemblers* (the programs that produce machine code from assembly) with different assembly languages, but only two x86 syntaxes are widely used. They are commonly called after the two companies that used them and had dominant influence on programming during that era:

- The *AT&T syntax*, used by default by all Linux tools.
- The *Intel syntax*, used by default... by Intel.

These syntaxes are also sometimes called *GAS* and *NASM* respectively, by the names of the two primary assemblers that use them (*GNU Assembler* and *Netwide Assembler*).

We used Intel syntax in this chapter. Here is how the summation loop looks like in AT&T asm:

```asm
LOOP:
    addl (%rax), %edx
    addq $4, %rax
    cmpq %rcx, %rax
    jne  LOOP
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

## Assembly Idioms

Lastly, there are a few "WTF is this" idioms in assembly language that felt wrong not to include in this chapter:

- The `lea` ("load effective address") instruction performs memory addressing and stores the address itself in a register without doing any memory operations. While its intended usage if to get addresses of class fields, it is often used as a trick that would otherwise involve 1 multiplication and 2 additions. For example, you can multiply by 3, 5 and 9 with it.
- `test rax, rax` is the optimal way to check if a value is zero. `test` instruction `and`s two values and sets flags according to the result. You can use `cmp rax, 0`, but it's machine code is one byte longer. This also implies that checking if a signed integer is exactly zero is slightly faster than checking if it is larger than zero.
- Likewise, `xor rax, rax` is the fastest way to set a register to zero.
- `xchg rax, rax` swaps a register with itself, and it is the official way to do nothing: `nop` maps to the same machine code. You may want to insert these operations to pad other instructions to specific addresses for a better memory layout, and we will talk about it in the next chapters.

If you think that this is hacky, unnatural and should be simplified, remember that just one level of abstraction away there is literally a rock that we tricked into thinking.
