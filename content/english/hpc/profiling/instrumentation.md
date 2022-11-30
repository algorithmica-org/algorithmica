---
title: Instrumentation
weight: 1
published: true
---

<!-- pv in Linux, pipes -->

*Instrumentation* is an overcomplicated term that means inserting timers and other tracking code into programs. The simplest example is using the `time` utility in Unix-like systems to measure the duration of execution for the whole program.

More generally, we want to know *which parts* of the program need optimization. There are tools shipped with compilers and IDEs that can time designated functions automatically, but it is more robust to do it by hand using any methods of interacting with time that the language provides:

```cpp
clock_t start = clock();
do_something();
float seconds = float(clock() - start) / CLOCKS_PER_SEC;
printf("do_something() took %.4f", seconds);
```

One nuance here is that you can't measure the execution time of particularly quick functions this way because the `clock` function returns the current timestamp in microseconds ($10^{-6}$) and also by itself takes up to a few hundred nanoseconds to complete. All other time-related utilities similarly have at least microsecond granularity, which is an eternity in the world of low-level optimization.

To achieve higher precision, you can invoke the function repeatedly in a loop, time the whole thing once, and then divide the total time by the number of iterations:

```cpp
#include <stdio.h>
#include <time.h>

const int N = 1e6;

int main() {
    clock_t start = clock();

    for (int i = 0; i < N; i++)
        clock(); // benchmarking the clock function itself

    float duration = float(clock() - start) / CLOCKS_PER_SEC;
    printf("%.2fns per iteration\n", 1e9 * duration / N);

    return 0;
}
```

You also need to ensure that nothing gets cached, optimized away by the compiler, or affected by similar side effects. This is a separate and highly complicated topic that we will discuss in more detail at [the end of the chapter](../benchmarking).

### Event Sampling

Instrumentation can also be used to collect other types of information that can give useful insights about the performance of a particular algorithm. For example:

- for a hash function, we are interested in the average length of its input;
- for a binary tree, we care about its size and height;
- for a sorting algorithm, we we want to know how many comparisons it does.

In a similar way, we can insert counters in the code that compute these algorithm-specific statistics.

Adding counters has the disadvantage of introducing overhead, although you can mitigate it almost completely by only doing it randomly for a small fraction of invocations:

```c++
void query() {
    if (rand() % 100 == 0) {
        // update statistics
    }
    // main logic
}
```

If the sample rate is small enough, the only remaining overhead per invocation will be random number generation and a condition check. Interestingly, we can optimize it a bit more with some stats magic.

Mathematically, what we are doing here is repeatedly sampling from [Bernoulli distribution](https://en.wikipedia.org/wiki/Bernoulli_distribution) (with $p$ equal to sample rate) until we get a success. There is another distribution that tells us how many iterations of Bernoulli sampling we need until the first positive, called [geometric distribution](https://en.wikipedia.org/wiki/Geometric_distribution). What we can do is to sample from it instead and use that value as a decrementing counter:

```c++
void query() {
    static next_sample = geometric_distribution(sample_rate);
    if (next_sample--) {
        next_sample = geometric_distribution(sample_rate);
        // ...
    }
    // ...
}
```

This way we can remove the need to sample a new random number on each invocation, only resetting the counter when we choose to calculate statistics.

Techniques like that are frequently used by library algorithm developers inside large projects to collect profiling data without affecting the performance of the end program too much.
