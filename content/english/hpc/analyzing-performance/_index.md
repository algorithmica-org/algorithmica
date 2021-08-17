---
title: Analyzing Performance
part: Performance Engineering
weight: 1
---

When I was in high school, during one of the summer breaks, I pushed myself to convert from being a JavaScript kiddie to becoming a competitive programmer. I realized that making websites won't get you into a university, but doing well in olympiads will. So I started learning C++ on my own and took the habit of solving (or at least trying to) a few problems from one of the online archives every day.

I was an okay programmer before, especially for a high school kid, but coming from a high-level langauge and only being involved in small web projects, I never really wondered how much time it took for my code to execute. But suddenly it started to matter: each problem has a strict time limit. I started counting my operations. How many can you do in one second?

You may have went through this in high school just as I did, or you might have learned that at a CS101 course in college, or maybe you even got through a decent chunk of your career without ever needing algorithms and then got asked to invert a binary tree on an interview. But regardless of background, if you are reading this book, you have asked that question too.

I didn't know much about computer architecture to answer this question. But I also didn't need the right answer; I needed a rule of thumb. So I thought "2-3GHz means that 2 to 3 billion instructions are executed every second, and in a simple loop that does something with array elements, I also need to do array indexing, increment loop counter, check end-of-loop condition and stuff like that, so let's add room for 3-5 more instructions for every useful one" and ended up with using $5 \cdot 10^8$ as an estimate. None of these statements are true, but counting how many operations my algorithm needed and dividing it by this number was a good rule of thumb in my use case.

The real answer, of course, is more complicated and highly dependent on the operation. It can be as low as $10^7$ if we are talking about chasing pointers in a random permutation or as high as $10^{11}$ if we are lighting up all the transistors we have to do some math-dense computation.

---

Processors have a concept of a *clock rate*, which refers to the frequency at which an electronic oscillator sends pulses through the curcuit, which change its state. Every *cycle*, something happens.

The clock rate is a variable. It may be adjusted during execution. For example, it frequently changes on mobile CPUs to consume lower energy most of the time and "burst" for a short period when it needs to do something compute-intensive.

The next two sections are about assembly and profiling. These don't seem fun or sexy. You may want to close the page, bookmark it in the browser and never come back. I'm trying to convince you, my reader.

One mistake I made when learning how to write faster programs is to use empirical approach. I actually wish I learned computer architecture before doing high-level programming. This would have saved me a few hundred hours.

"But I'm here to learn how to write faster algorithms, not to learn assembly"—you may say. Let me convince you otherwise.

## How Code Gets Executed

Processors can be thought of as state machines. They keep their state in multiple registers that store fixed-length data, one of which, instruction pointer, points to a location in memory in which these encoded instructions are stored.

There are multiple ways how code in a programming language can get executed. This depends on the type of a language.

From programmer's perspective, there are two types of languages: *compiled* and *interpreted*.

From computer's perspective, there are also two types of languages: *native* and *managed*.

The difference is that the first classification is about having to pre-process a program before execution, and the second is about directly executing machine code or having some sort of a runtime.

Since running machine code in an interpreter doesn't make sense, there are 3 types of languages in total:

- Interpreted languages, such as Python, JavaScript or Ruby.
- Compiled languages with a runtime, such as Java, C# or Erlang (and languages that work on their VMs, like Scala, F# and Elixir).
- Compiled native languages, such as C, Go and Rust.

How compilation happens.

Interpreters and virtual machines are more flexible and can support nice high-level programming features — such as dynamic code alteration — at the cost of performance.

Euclid's algorithm for calculating GCD[^gcd]:

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

630 seconds — more than 10 minutes! I had to go pour myself some tea.

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

10 seconds. `pypy` it takes about 12 seconds.

```c
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

const int n = 1024;
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

    float seconds = float(clock() - start) / CLOCKS_PER_SEC;
    printf("%.4f\n", seconds);
    
    return 0;
}
```

9 seconds when you compile with `gcc -O3`, but when you add `-march=native` and `-ffast=math` flags, it goes down to 0.6 seconds

Let's go back to Python. The easiest way to use BLAS is to call it from `numpy`:

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

It now takes ~0.12 seconds — that's 5x speedup over C++ version and 5000x speedup over Python.

You don't typically see such dramatic improvements.

Theoretical peak for a single core is ~22.4 GFLOPS. We are doing about 18.

They aren't always sacrificing control because of a trick called just-in-time compilation. If you tune the runtime right, then for frequent procedures a native code is compiled, which is.

My point here is that using a native language doesn't give you performance; it gives you *control* over performance. And to make use of that control, having an intuition about performance isn't enough; it is instrumental to understand CPU microarchitecture.
