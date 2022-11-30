---
title: Functions and Recursion
weight: 3
published: true
---

To "call a function" in assembly, you need to [jump](../loops) to its beginning and then jump back. But then two important problems arise:

1. What if the caller stores data in the same registers as the callee?
2. Where is "back"?

Both of these concerns can be solved by having a dedicated location in memory where we can write all the information we need to return from the function before calling it. This location is called *the stack*.

### The Stack

The hardware stack works the same way software stacks do and is similarly implemented as just two pointers:

- The *base pointer* marks the start of the stack and is conventionally stored in `rbp`.
- The *stack pointer* marks the last element of the stack and is conventionally stored in `rsp`.

When you need to call a function, you push all your local variables onto the stack (which you can also do in other circumstances; e.g., when you run out of registers), push the current instruction pointer, and then jump to the beginning of the function. When exiting from a function, you look at the pointer stored on top of the stack, jump there, and then carefully read all the variables stored on the stack back into their registers.

<!--

Function parameters and local variables are accessed by adding and subtracting, respectively, a constant offset from `ebp`.

ebp itself actually points to the previous frame's base pointer, which enables stack walking in a debugger and viewing other frames local variables to work. Fun things, such as stopping the program and seeing which functions are called by which.

push ebp      ; Preserve current frame pointer
mov ebp, esp  ; Create new frame pointer pointing to current stack top
sub esp, 20   ; allocate 20 bytes worth of locals on stack.

frame pointer omission optimization which you can enable will actually eliminate this and use ebp as another register and access locals directly off of esp, but this makes debugging a bit more difficult since the debugger can no longer directly access the stack frames of earlier function calls.

When a function starts, it executed a *function prologue*: saves the previous base pointer on the stack and sets `rbp = rsp`.

-->

You can implement all that with the usual memory operations and jumps, but because of how frequently it is used, there are 4 special instructions for doing this:

- `push` writes data at the stack pointer and decrements it.
- `pop` reads data from the stack pointer and increments it.
- `call` puts the address of the following instruction on top of the stack and jumps to a label.
- `ret` reads the return address from the top of the stack and jumps to it.

You would call them "syntactic sugar" if they weren't actual hardware instructions — they are just fused equivalents of these two-instruction snippets:

```nasm
; "push rax"
sub rsp, 8
mov QWORD PTR[rsp], rax

; "pop rax"
mov rax, QWORD PTR[rsp]
add rsp, 8

; "call func"
push rip ; <- instruction pointer (although accessing it like that is probably illegal)
jmp func

; "ret"
pop  rcx ; <- choose any unused register
jmp rcx
```

The memory region between `rbp` and `rsp` is called a *stack frame*, and this is where local variables of functions are typically stored. It is pre-allocated at the start of the program, and if you push more data on the stack than its capacity (8MB by default on Linux), you encounter a *stack overflow* error. Because modern operating systems don't actually give you memory pages until you read or write to their address space, you can freely specify a very large stack size, which acts more like a limit on how much stack memory can be used, and not a fixed amount every program has to use.

<!--

It is convenient to save the frame pointer `rbp` at the beginning of a function and replace it with `rsp` — this way, when leaving a function, you could just restore `rbp` and forget about all its local variables. This sequence is called *function prologue* and usually looks somewhat like that (which is often optimized away by the compiler):

```nasm
push rbp     ; preserve the current frame pointer
mov rbp, rsp ; create a new frame pointer pointing to the current top of the stack
sub rsp, 20  ; allocate 20 bytes worth of locals on stack
```

-->

<!--
The memory region dedicated for stack memory (called *stack frame*) is not any different from any other memory region. It is allocated on the start of the program. You could also do tricky stuff, such as 

Functions execute a *prologue* which usually looks somewhat like that:

```nasm
push rbp     ; preserve the current frame pointer
mov rbp, rsp ; create a new frame pointer pointing to the current top of the stack
sub rsp, 20  ; allocate 20 bytes worth of locals on stack
```

Note that the data in the stack is written top-to-bottom. This is just a convention: it could be the other way around. When you need to "leave" a function or a visibility scope such as the body of an `if` or a `for`, you can just increase the stack pointer.

-->

### Calling Conventions

The people who develop compilers and operating systems eventually came up with [conventions](https://wiki.osdev.org/Calling_Conventions) on how to write and call functions. These conventions enable some important [software engineering marvels](/hpc/compilation/stages/) such as splitting compilation into separate units, reusing already-compiled libraries, and even writing them in different programming languages.

Consider the following example in C:

```c
int square(int x) {
    return x * x;
}

int distance(int x, int y) {
    return square(x) + square(y);
}
```

<!--

When compiled without any optimization flags, it produces the following assembly:

```nasm
square:
    push    rbp
    mov     rbp, rsp
    mov     DWORD PTR [rbp-4], edi
    mov     eax, DWORD PTR [rbp-4]
    imul    eax, eax
    pop     rbp
    ret
length:
    push    rbp
    mov     rbp, rsp
    push    rbx
    sub     rsp, 8
    mov     DWORD PTR [rbp-12], edi
    mov     DWORD PTR [rbp-16], esi
    mov     eax, DWORD PTR [rbp-12]
    mov     edi, eax
    call    square
    mov     ebx, eax
    mov     eax, DWORD PTR [rbp-16]
    mov     edi, eax
    call    square
    add     eax, ebx
    mov     rbx, QWORD PTR [rbp-8]
    leave
    ret
```
-->

By convention, a function should take its arguments in `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9` (and the rest in the stack if those weren't enough), put the return value into `rax`, and then return. Thus, `square`, being a simple one-argument function, can be implemented like this:

```nasm
square:             ; x = edi, ret = eax
    imul edi, edi
    mov  eax, edi
    ret
```

Each time we call it from `distance`, we just need to go through some trouble preserving its local variables:

```nasm
distance:           ; x = rdi/edi, y = rsi/esi, ret = rax/eax
    push rdi
    push rsi
    call square     ; eax = square(x)
    pop  rsi
    pop  rdi

    mov  ebx, eax   ; save x^2
    mov  rdi, rsi   ; move new x=y

    push rdi
    push rsi
    call square     ; eax = square(x=y)
    pop  rsi
    pop  rdi

    add  eax, ebx   ; x^2 + y^2
    ret
```

There are a lot more nuances, but we won't go into detail here because this book is about performance, and the best way to deal with functions calls is actually to avoid making them in the first place.

### Inlining

Moving data to and from the stack creates noticeable overhead for small functions like these. The reason you have to do this is that, in general, you don't know whether the callee is modifying the registers where you store your local variables. But when you have access to the code of `square`, you can solve this problem by stashing the data in registers that you know won't be modified.

```nasm
distance:
    call square
    mov  ebx, eax
    mov  edi, esi
    call square
    add  eax, ebx
    ret
```

This is better, but we are still implicitly accessing stack memory: you need to push and pop the instruction pointer on each function call. In simple cases like this, we can *inline* function calls by stitching the callee's code into the caller and resolving conflicts over registers. In our example:

```nasm
distance:
    imul edi, edi       ; edi = x^2
    imul esi, esi       ; esi = y^2
    add  edi, esi
    mov  eax, edi       ; there is no "add eax, edi, esi", so we need a separate mov
    ret
```

This is fairly close to what optimizing compilers produce out of this snippet — only they use the [lea trick](../assembly) to make the resulting machine code sequence a few bytes smaller:

```nasm
distance:
    imul edi, edi       ; edi = x^2
    imul esi, esi       ; esi = y^2
    lea  eax, [rdi+rsi] ; eax = x^2 + y^2
    ret
```

In situations like these, function inlining is clearly beneficial, and compilers mostly do it [automatically](/hpc/compilation/situational), but there are cases when it's not — and we will talk about them [in a bit](../layout).

### Tail Call Elimination

Inlining is straightforward to do when the callee doesn't make any other function calls, or at least if these calls are not recursive. Let's move on to a more complex example. Consider this recursive computation of a factorial:

```cpp
int factorial(int n) {
    if (n == 0)
        return 1;
    return factorial(n - 1) * n;
}
```

Equivalent assembly:

```nasm
; n = edi, ret = eax
factorial:
    test edi, edi   ; test if a value is zero
    jne  nonzero    ; (the machine code of "cmp rax, 0" would be one byte longer)
    mov  eax, 1     ; return 1
    ret
nonzero:
    push edi        ; save n to use later in multiplication
    sub  edi, 1
    call factorial  ; call f(n - 1)
    pop  edi
    imul eax, edi
    ret
```

If the function is recursive, it is still often possible to make it "call-less" by restructuring it. This is the case when the function is *tail recursive*, that is, it returns right after making a recursive call. Since no actions are required after the call, there is also no need for storing anything on the stack, and a recursive call can be safely replaced with a jump to the beginning — effectively turning the function into a loop.

To make our `factorial` function tail-recursive, we can pass a "current product" argument to it:

```cpp
int factorial(int n, int p = 1) {
    if (n == 0)
        return p;
    return factorial(n - 1, p * n);
}
```

Then this function can be easily folded into a loop:

```nasm
; assuming n > 0
factorial:
    mov  eax, 1
loop:
    imul eax, edi
    sub  edi, 1
    jne  loop
    ret
```

The primary reason why recursion can be slow is that it needs to read and write data to the stack, while iterative and tail-recursive algorithms do not. This concept is very important in functional programming, where there are no loops and all you can use are functions. Without tail call elimination, functional programs would require way more time and memory to execute.
