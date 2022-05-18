---
title: Programming Languages
aliases:
  - /hpc/analyzing-performance
weight: 2
published: true
---

If you are reading this book, then somewhere on your computer science journey you had a moment when you first started to care about the efficiency of your code.

Mine was in high school, when I realized that making websites and doing *useful* programming won't get you into a university, and entered the exciting world of algorithmic programming olympiads. I was an okay programmer, especially for a highschooler, but I had never really wondered how much time it took for my code to execute before. But suddenly it started to matter: each problem now has a strict time limit. I started counting my operations. How many can you do in one second?

I didn't know much about computer architecture to answer this question. But I also didn't need the right answer — I needed a rule of thumb. My thought process was: "2-3GHz means 2 to 3 billion instructions executed every second, and in a simple loop that does something with array elements, I also need to increment loop counter, check end-of-loop condition, do array indexing and stuff like that, so let's add room for 3-5 more instructions for every useful one" and ended up with using $5 \cdot 10^8$ as an estimate. None of these statements are true, but counting how many operations my algorithm needed and dividing it by this number was a good rule of thumb for my use case.

The real answer, of course, is much more complicated and highly dependent on what kind of "operation" you have in mind. It can be as low as $10^7$ for things like [pointer chasing](/hpc/cpu-cache/latency) and as high as $10^{11}$ for [SIMD-accelerated](/hpc/simd) linear algebra. To demonstrate these striking differences, we will use the case study of matrix multiplication implemented in different languages — and dig deeper into how computers execute them.

<!--

Because of this logic, and also because of the [computation model](../) postulated in CS 101, many programmers have a misconception that computers can execute a certain number of "operations" per second, and that using different programming languages has some sort of [multiplier effect](https://benchmarksgame-team.pages.debian.net/benchmarksgame/index.html) on that number:

- "you can execute about $5 \cdot 10^8$ operations per second on this machine,"
- "C is 2 times faster than Java,"
- "Python is 100x slower than C++."

-->

## Types of Languages

<!--

Processors can be thought of as *state machines*. They keep their *state* in several fixed-length *registers*, one of which, the instruction pointer, indicates a memory location of the next instruction to be read and executed. This instruction somehow modifies the registers and moves the instruction pointer to the next instruction to be executed, and so on.

These instructions — called *machine code* — are binary encoded, quirky and very difficult to work with, so no sane person writes them directly nowadays. Instead, we use higher-level programming languages and employ alternative means to feed instructions to the processor.

-->

On the lowest level, computers execute *machine code* consisting of binary-encoded *instructions* which are used to control the CPU. They are specific, quirky, and require a great deal of intellectual effort to work with, so one of the first things people did after creating computers was create *programming languages*, which abstract away some details of how computers operate to simplify the process of programming.

A programming language is fundamentally just an interface. Any program written in it is just a nicer higher-level representation which still at some point needs to be transformed into the machine code to be executed on the CPU — and there are several different means of doing that:

- From a programmer's perspective, there are two types of languages: *compiled*, which pre-process before executing, and *interpreted*, which are executed during runtime using a separate program called *an interpreter*.
- From a computer's perspective, there are also two types of languages: *native*, which directly execute machine code, and *managed*, which rely on some sort of *runtime* to do it.

Since running machine code in an interpreter doesn't make sense, this makes a total of three types of languages:

- Interpreted languages, such as Python, JavaScript, or Ruby.
- Compiled languages with a runtime, such as Java, C#, or Erlang (and languages that work on their VMs, such as Scala, F#, or Elixir).
- Compiled native languages, such as C, Go, or Rust.

There is no "right" way of executing computer programs: each approach has its own gains and drawbacks. Interpreters and virtual machines provide flexibility and enable some nice high-level programming features such as dynamic typing, run time code alteration, and automatic memory management, but these come with some unavoidable performance trade-offs, which we will now talk about.

### Interpreted languages

Here is an example of a by-definition $1024 \times 1024$ matrix multiplication in pure Python:

```python
import time
import random

n = 1024

a = [[random.random()
      for row in range(n)]
      for col in range(n)]

b = [[random.random()
      for row in range(n)]
      for col in range(n)]

c = [[0
      for row in range(n)]
      for col in range(n)]

start = time.time()

for i in range(n):
    for j in range(n):
        for k in range(n):
            c[i][j] += a[i][k] * b[k][j]

duration = time.time() - start
print(duration)
```

This code runs in 630 seconds. That's more than 10 minutes!

Let's try to put this number in perspective. The CPU that ran it has a clock frequency of 1.4GHz, meaning that it does $1.4 \cdot 10^9$ cycles per second, totaling to almost $10^{15}$ for the entire computation, and about 880 cycles per multiplication in the innermost loop.

This is not surprising if you consider the things that Python needs to do to figure out what the programmer meant:

- it parses the expression `c[i][j] += a[i][k] * b[k][j]`;
- tries to figure out what `a`, `b`, and `c` are and looks up their names in a special hash table with type information;
- understands that `a` is a list, fetches its `[]` operator, retrieves the pointer for `a[i]`, figures out it's also a list, fetches its `[]` operator again, gets the pointer for `a[i][k]`, and then the element itself;
- looks up its type, figures out that it's a `float`, and fetches the method implementing `*` operator;
- does the same things for `b` and `c` and finally add-assigns the result to `c[i][j]`.

Granted, the interpreters of widely used languages such as Python are well-optimized, and they can skip through some of these steps on repeated execution of the same code. But still, some quite significant overhead is unavoidable due to the language design. If we get rid of all this type checking and pointer chasing, perhaps we can get cycles per multiplication ratio closer to 1, or whatever the "cost" of native multiplication is?

### Managed Languages

The same matrix multiplication procedure, but implemented in Java:

```java
import java.util.Random;

public class Matmul {
    static int n = 1024;
    static double[][] a = new double[n][n];
    static double[][] b = new double[n][n];
    static double[][] c = new double[n][n];

    public static void main(String[] args) {
        Random rand = new Random();

        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                a[i][j] = rand.nextDouble();
                b[i][j] = rand.nextDouble();
                c[i][j] = 0;
            }
        }

        long start = System.nanoTime();

        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                for (int k = 0; k < n; k++)
                    c[i][j] += a[i][k] * b[k][j];
                
        double diff = (System.nanoTime() - start) * 1e-9;
        System.out.println(diff);
    }
}
```

It now runs in 10 seconds, which amounts to roughly 13 CPU cycles per multiplication — 63 times faster than Python. Considering that we need to read elements of `b` non-sequentially from the memory, the running time is roughly what it is supposed to be.

Java is a *compiled*, but not *native* language. The program first compiles to *bytecode*, which is then interpreted by a virtual machine (JVM). To achieve higher performance, frequently executed parts of the code, such as the innermost `for` loop, are compiled into the machine code during runtime and then executed with almost no overhead. This technique is called *just-in-time compilation*.

JIT compilation is not a feature of the language itself, but of its implementation. There is also a JIT-compiled version of Python called [PyPy](https://www.pypy.org/), which needs about 12 seconds to execute the code above without any changes to it.

### Compiled Languages

Now it's turn for C:

```cpp
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#define n 1024
double a[n][n], b[n][n], c[n][n];

int main() {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            a[i][j] = (double) rand() / RAND_MAX;
            b[i][j] = (double) rand() / RAND_MAX;
        }
    }

    clock_t start = clock();

    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                c[i][j] += a[i][k] * b[k][j];

    float seconds = (float) (clock() - start) / CLOCKS_PER_SEC;
    printf("%.4f\n", seconds);
    
    return 0;
}
```

It takes 9 seconds when you compile it with `gcc -O3`.

It doesn't seem like a huge improvement — the 1-3 second advantage over Java and PyPy can be attributed to the additional time of JIT-compilation — but we haven't yet taken advantage of a far better C compiler ecosystem. If we add `-march=native` and `-ffast-math` flags, time suddenly goes down to 0.6 seconds!

What happened here is we [communicated to the compiler](/hpc/compilation/flags/) the exact model of the CPU we are running (`-march=native`) and gave it the freedom to rearrange [floating-point computations](/hpc/arithmetic/float) (`-ffast-math`), and so it took advantage of it and used [vectorization](/hpc/simd) to achieve this speedup.

It's not like it is impossible to tune the JIT-compilers of PyPy and Java to achieve the same performance without significant changes to the source code, but it is certainly easier for languages that compile directly to native code.

### BLAS

Finally, let's take a look at what an expert-optimized implementation is capable of. We will test a widely-used optimized linear algebra library called [OpenBLAS](https://www.openblas.net/). The easiest way to use it is to go back to Python and just call it from `numpy`:

```python
import time
import numpy as np

n = 1024

a = np.random.rand(n, n)
b = np.random.rand(n, n)

start = time.time()

c = np.dot(a, b)

duration = time.time() - start
print(duration)
```

Now it takes ~0.12 seconds: a ~5x speedup over the auto-vectorized C version and ~5250x speedup over our initial Python implementation!

You don't typically see such dramatic improvements. For now, we are not ready to tell you exactly how this is achieved. Implementations of dense matrix multiplication in OpenBLAS are typically [5000 lines of handwritten assembly](https://github.com/xianyi/OpenBLAS/blob/develop/kernel/x86_64/dgemm_kernel_16x2_haswell.S) tailored separately for *each* architecture. In later chapters, we will explain all the relevant techniques one by one, and then [return](/hpc/algorithms/matmul) to this example and develop our own BLAS-level implementation using just under 40 lines of C.

### Takeaway

The key lesson here is that using a native, low-level language doesn't necessarily give you performance; but it does give you *control* over performance.

Complementary to the "N operations per second" simplification, many programmers also have a misconception that using different programming languages has some sort of multiplier on that number. Thinking this way and [comparing languages](https://benchmarksgame-team.pages.debian.net/benchmarksgame/index.html) in terms of performance doesn't make much sense: programming languages are fundamentally just tools that take away *some* control over performance in exchange for convenient abstractions.  Regardless of the execution environment, it is still largely a programmer's job to use the opportunities that the hardware provides.
