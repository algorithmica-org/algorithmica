---
title: Benchmarking
weight: 6
---

Most good software engineering practices in one way or another address the issue of making *development cycles* faster: you want to compile your software faster (build systems), catch bugs as soon as possible (static analysis, continuous integration), release as soon as the new version is ready (continuous deployment), and react to user feedback without much delay (agile development).

Performance engineering is not different. If you do it correctly, it should also resemble a cycle:

1. Run the program and collect metrics.
2. Figure out where the bottleneck is.
3. Remove the bottleneck and go to step 1.

In this section, we will talk about benchmarking and discuss some practical techniques that make this cycle shorter and help you iterate faster. Most of the advice comes from working on this book, so you can find many real examples of described setups in the [code repository](https://github.com/sslotin/ahm-code) for this book.

### Benchmarking Inside C++

There are several approaches to writing benchmarking code. Perhaps the most popular one is to include several same-language implementations you want to compare in one file, separately invoke them from the `main` function, and calculate all the metrics you want in the same source file.

The disadvantage of this method is that you need to write a lot of boilerplate code and duplicate it for each implementation, but it can be partially neutralized with metaprogramming. For example, when you are benchmarking multiple [gcd](/hpc/algorithms/gcd) implementations, you can reduce benchmarking code considerably with this higher-order function:

```c++
const int N = 1e6, T = 1e9 / N;
int a[N], b[N];

void timeit(int (*f)(int, int)) {
    clock_t start = clock();

    int checksum = 0;

    for (int t = 0; t < T; t++)
        for (int i = 0; i < n; i++)
            checksum ^= f(a[i], b[i]);
    
    float seconds = float(clock() - start) / CLOCKS_PER_SEC;

    printf("checksum: %d\n", checksum);
    printf("%.2f ns per call\n", 1e9 * seconds / N / T);
}

int main() {
    for (int i = 0; i < N; i++)
        a[i] = rand(), b[i] = rand();
    
    timeit(std::gcd);
    timeit(my_gcd);
    timeit(my_another_gcd);
    // ...

    return 0;
}
```

This is a very low-overhead method that lets you run more experiments and [get more accurate results](../noise) from them. You still have to perform some repeated actions, but they can be largely automated with frameworks, [Google benchmark library](https://github.com/google/benchmark) being the most popular choice for C++. Some programming languages also have handy built-in tools for benchmarking: special mention here goes to [Python's timeit function](https://docs.python.org/3/library/timeit.html) and [Julia's @benchmark macro](https://github.com/JuliaCI/BenchmarkTools.jl).

Although *efficient* in terms of execution speed, C and C++ are not the most *productive* languages, especially when it comes to analytics. When your algorithm depends on some parameters such as the input size, and you need to collect more than just one data point from each implementation, you really want to integrate your benchmarking code with the outside environment and analyze the results using something else.

### Splitting Up Implementations

One way to improve modularity and reusability is to separate all testing and analytics code from the actual implementation of the algorithm, and also make it so that different versions are implemented in separate files, but have the same interface.

In C/C++, you can do this by creating a single header file (e.g., `gcd.hh`) with a function interface and all its benchmarking code in `main`:

```c++
int gcd(int a, int b); // to be implemented

// for data structures, you also need to create a setup function
// (unless the same preprocessing step for all versions would suffice)

int main() {
    const int N = 1e6, T = 1e9 / N;
    int a[N], b[N];
    // careful: local arrays are allocated on the stack and may cause stack overflow
    // for large arrays, allocate with "new" or create a global array

    for (int i = 0; i < N; i++)
        a[i] = rand(), b[i] = rand();

    int checksum = 0;

    clock_t start = clock();

    for (int t = 0; t < T; t++)
        for (int i = 0; i < n; i++)
            checksum += gcd(a[i], b[i]);
    
    float seconds = float(clock() - start) / CLOCKS_PER_SEC;

    printf("%d\n", checksum);
    printf("%.2f ns per call\n", 1e9 * seconds / N / T);
    
    return 0;
}
```

Then you create many implementation files for each algorithm version (e.g., `v1.cc`, `v2.cc`, and so on, or some meaningful names if applicable) that all include that single header file:

```c++
#include "gcd.hh"

int gcd(int a, int b) {
    if (b == 0)
        return a;
    else
        return gcd(b, a % b);
}
```

The whole purpose of doing this is to be able to benchmark a specific algorithm version from the command line without touching any source code files. For this purpose, you may also want to expose any parameters that it may have — for example, by parsing them from the command line arguments:

```c++
int main(int argc, char* argv[]) {
    int N = (argc > 1 ? atoi(argv[1]) : 1e6);
    const int T = 1e9 / N;

    // ...
}
```

Another way to do it is to use C-style global defines and then pass them with the `-D N=...` flag during compilation:

```c++
#ifndef N
#define N 1000000
#endif

const int T = 1e9 / N;
```

This way you can make use of compile-time constants, which may be very beneficial for the performance of some algorithms, at the expense of having to re-build the program each time you want to change the parameter, which considerably increases the time you need to collect metrics across a range of parameter values.

### Makefiles

<!-- TODO -->

Splitting up source files allows you to speed up compilation using a caching build system such as [Make](https://en.wikipedia.org/wiki/Make_(software)).

I usually carry a version of this Makefile across my projects:

```c++
compile = g++ -std=c++17 -O3 -march=native -Wall

%: %.cc gcd.hh
	$(compile) $< -o $@ 

%.s: %.cc gcd.hh
	$(compile) -S -fverbose-asm $< -o $@

%.run: %
	@./$<

.PHONY: %.run
```

You can now compile `example.cc` with `make example`, and automatically run it with `make example.run`. 

You can also add scripts for calculating statistics in the Makefile, or incorporate it with `perf stat` calls to make profiling automatic.

### Jupyter Notebooks

To speed up high-level analytics, you can create a Jupyter notebook where you put all your scripts and do all the plots.

It is convenient to add a wrapper for benchmarking an implementation, which just returns a scalar result:

```python
def bench(source, n=2**20):
    !make -s {source}
    if _exit_code != 0:
        raise Exception("Compilation failed")
    res = !./{source} {n} {q}
    duration = float(res[0].split()[0])
    return duration
```

Then you can use it to write clean analytics code:

```python
ns = list(int(1.17**k) for k in range(30, 60))
baseline = [bench('std_lower_bound', n=n) for n in ns]
results = [bench('my_binary_search', n=n) for n in ns]

# plotting relative speedup for different array sizes
import matplotlib.pyplot as plt

plt.plot(ns, [x / y for x, y in zip(baseline, results)])
plt.show()
```

Once established, this workflow makes you iterate much faster and focus on optimizing the algorithm itself.
