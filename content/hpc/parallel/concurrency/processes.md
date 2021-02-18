---
title: Processes
weight: 1
---

It works well when you need.

Fork system call is used for creating a new process, which is called child process, which runs concurrently with the process that makes the fork() call (parent process). After a new child process is created, both processes will execute the next instruction following the fork() system call. A child process uses the same pc(program counter), same CPU registers, same open files which use in the parent process.

It takes no parameters and returns an integer value. Below are different values returned by fork().

```cpp
#include <stdio.h> 
#include <sys/types.h> 
#include <unistd.h> 
int main() { 
    // make two process which run same 
    // program after this instruction 
    fork(); 
  
    printf("Hello world!\n"); 
    return 0; 
} 
```

Major disadvantage is the extra cost. It is managed by the operating system. Separate processes are used when you need such granularity.

Forked processes can neither see nor alter the memory space of each other.
