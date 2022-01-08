---
title: Computer Architecture
alias: /hpc/analyzing-performance
weight: 2
---

If you are reading this book, then somewhere on your computer science journey you had a moment when you first started to care about efficiency of your code.

Mine was in high school, when I entered the world of competitive programming and started learning C++. I was happily coding small projects in JavaScript and PHP before that, but I realized that making websites won't get you into a university, but doing well in olympiads will.

I was an okay programmer, especially for a highschooler, but coming from high-level languages, I had never really wondered how much time it took for my code to execute. But suddenly it started to matter: each problem now has a strict time limit. I started counting my operations. How many can you do in one second?

I didn't know much about computer architecture to answer this question. But I also didn't need the right answer — I needed a rule of thumb. My thought process was: "2-3GHz means 2 to 3 billion instructions executed every second, and in a simple loop that does something with array elements, I also need to increment loop counter, check end-of-loop condition, do array indexing and stuff like that, so let's add room for 3-5 more instructions for every useful one" and ended up with using $5 \cdot 10^8$ as an estimate. None of these statements are true, but counting how many operations my algorithm needed and dividing it by this number was a good rule of thumb for my use case.

The real answer is, of course, much more complicated and highly dependent on what kind of "operation" you have in mind. It can be as low as $10^7$ for pointer chasing and as high as $10^{11}$ for dense linear algebra. To demonstrate these striking differences, we will use the case study of matrix multiplication implemented in different languages.

## How Code Gets Executed

Processors can be thought of as state machines. They keep their state in several fixed-length registers, one of which, the instruction pointer, indicates a memory location of the next instruction to be read and executed. This instruction somehow modifies the registers and moves the instruction pointer to the next instruction to be executed, and so on.

These instructions — called *machine code* — are binary encoded, quirky and very difficult to work with, so no sane person writes them directly nowadays. Instead, we use higher-level programming languages and employ alternative means to feed instructions to the processor.

From programmer's perspective, there are two types of languages: *compiled* and *interpreted*. The former you have to pre-process before executing, while the latter are executed during runtime using an *interpreter*.

From computer's perspective, there are also two types of languages: *native* and *managed*. The former directly execute machine code, while the latter use some sort a *runtime* to do so. 

Since running machine code in an interpreter doesn't make sense, there are in total three types of languages:

- Interpreted languages, such as Python, JavaScript or Ruby.
- Compiled languages with a runtime, such as Java, C# or Erlang (and languages that work on their VMs, such as Scala, F# or Elixir).
- Compiled native languages, such as C, Go or Rust.

Interpreters and virtual machines provide flexibility and enable some nice high-level programming features such as dynamic code alteration. Unfortunately, there are also unavoidable trade-offs between performance and the benefits that dynamic languages can provide.

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

Let's try to put this number in perspective. The CPU that ran it has a clock frequency of 1.4GHz, meaning that it does $1.4 \cdot 10^9$ cycles per second, almost $10^{15}$ for the entire computation, and 880 cycles per each multiplication in the innermost loop.

This is not surprising if you consider the things that Python needs to do to figure out what the programmer meant:

- it parses the expression `c[i][j] += a[i][k] * b[k][j]`;
- tries to figure out what `a`, `b`, and `c` are and looks up their names in a special hash table with type information;
- understands that `a` is a list, fetches its `[]` operator, retrieves the pointer for `a[i]`, figures out it's also a list, fetches its `[]` operator again, gets the pointer for `a[i][k]`, and then the element itself;
- looks up its type, figures out that it's a `float`, and fetches the method implementing `*` operator;
- does the same things for `b` and `c` and finally add-assigns the result to `c[i][j]`.

If we get rid of all this type checking and pointer chasing, perhaps we can get cycles per multiplication ratio to 1, or whatever the cost of native multiplication is?

### Managed Languages

Here is the same matrix multiplication, but implemented in Java:

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

It now runs in 10 seconds, or roughly 13 cycles per multiplication. Considering that we need to read elements of `b` non-sequentially form memory, the running time is roughly what it is supposed to be.

Note that Java is a compiled, but not native language. The code compiles to bytecode, which is then interpreted by a virtual machine (JVM). To achieve higher performance, frequently executed parts of the code, such as the innermost for loop, are compiled into machine code during runtime and executed with almost no overhead. This technique is called *just-in-time compilation*.

JIT compilation is not a feature of the language itself, of its implementation. There is also a JIT-compiled version of Python called [PyPy](https://www.pypy.org/), which needs about 12 seconds to execute the code above without any changes.

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

It takes 9 seconds when you compile it with `gcc -O3`. The 1-3 second advantage over Java and PyPy can be explained as the additional time of JIT-compilation. It doesn't seem like a lot, but we haven't yet taken advantage of a far better C compiler ecosystem. If we add `-march=native` and `-ffast=math` flags, time suddenly goes down to 0.6 seconds!

What happened here is we communicated the compiler the exact model of CPU we are running (`-march=native`) and gave it freedom to rearrange floating-point computations (`-ffast=math`), and so it took advantage of it, most importantly using vectorization — an architecture-specific technique we will study in detail later in chapter 3.

### BLAS

Finally, let's look what an expert-optimized implementation is capable of. We will test an optimized linear algebra library called [OpenBLAS](https://www.openblas.net/). The easiest way to use it is to go back to Python and call it from `numpy`:

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

Now it takes ~0.12 seconds: a ~5x speedup over C++ and ~5250x speedup over our initial Python implementation!

You don't typically see such dramatic improvements. For now, we are not ready to tell you exactly how this is achieved. Implementations of dense matrix multiplication in OpenBLAS are typically [5000 lines of handwritten assembly](https://github.com/xianyi/OpenBLAS/blob/develop/kernel/x86_64/dgemm_kernel_16x2_haswell.S) for *each* architecture. In later chapters, we will explain all the relevant techniques one by one, and in chapter 6, we will return to this example and develop our own BLAS-level implementation with just under 40 lines of C.

The point here is that using a native language doesn't give you performance; it gives you *control* over performance. And to make use of it, having just a general intuition about performance isn't enough. It is instrumental to understand CPU microarchitecture, which is what we will focus on in this chapter.
