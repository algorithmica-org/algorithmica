---
title: Interrupts and System Calls
weight: 9
draft: true
---

```asm
global _start

section .text

_start:
  mov rax, 1        ; write(
  mov rdi, 1        ;   STDOUT_FILENO,
  mov rsi, msg      ;   "Hello, world!\n",
  mov rdx, msglen   ;   sizeof("Hello, world!\n")
  syscall           ; );

  mov rax, 60       ; exit(
  mov rdi, 0        ;   EXIT_SUCCESS
  syscall           ; );

section .rodata
  msg: db "Hello, world!", 10
  msglen: equ $ - msg
```

Interrupts are costly. They are not supposed to be on the normal execution path. Exceptions.

There is some overhead associated with doing system calls, so they are usually avoided. For example, all I/O is usually buffered, so that you send a single, say, 4KB piece of data to the OS.
