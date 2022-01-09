---
title: Functions and Recursion
weight: 3
---


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

Over time, people who develop compilers and operating systems came up with [conventions](https://en.wikipedia.org/wiki/X86_calling_conventions) on how to call functions. These conventions allow software engineering marvels such as splitting compilation into separate units, re-using already compiled libraries and even writing them in different programming languages. Of course, you don't have to follow these conventions in local functions.

There are a lot more nuances, but we won't go in detail here, because this book is about performance, and the best way to deal with functions calls is actually to avoid making them in the first place.

### Overhead of Recursion

Moving data to and from the stack creates a huge overhead for smaller functions. When possible, optimizing compilers will *inline* function calls by stitching callee's code into the caller and resolving conflicts over registers. This is straightforward to do when callee doesn't make any other function calls, or at least if these calls are not recursive.

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
