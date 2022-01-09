---
title: The Cost of Branching
weight: 2
---

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
