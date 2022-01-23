---
title: Benchmarking
weight: 6
---

(This is an early draft. Don't read it.)

Performance cycle is implementing, running and collecting metrics, and finding where the bottleneck is. The shorter this cycle is, the better.

If you do it correctly, working on improving performance should resemble a loop:

1. run the program and collect metrics,
2. figure out where the bottleneck is,
3. remove the bottleneck and go to step 1.

The shorter this loop is, the faster you will iterate.

Faster — and accurate — as possible.

### Managing Experiments

This isn't the universally best approach, but this is what I do. For something smaller, you may use this:

```c++

```

Here are some hints on how to set up your environment to achieve this (you can find many examples in the [code repo](https://github.com/sslotin/ahm-code) for this book):

- Separate all testing and analytics code from the implementation of the algorithm itself, and also different implementations from each other. In C/C++, you can do this by creating a single header file (e. g. `matmul.hh`) with a function interface and the code for its benchmarking in `main`, and many implementation files for each algorithm version (`v1.cc`, `v2.cc`, etc.) that all include that single header file.
- To speed up builds and reruns, create a Makefile or just a bunch of small scripts that calculate the statistics you may need.
- To speed up high-level analytics, create a Jupyter notebook where you put small scripts and do all the plots. You can also put build scripts there if you feel like it.

https://github.com/google/benchmark

Using C-style global defines instead of `const int`.

```c++
#include <stdio.h>
#include <time.h>

const int N = 1e6;

#ifndef N
#define N (1<<20)
#endif
int main(int argc, char* argv[]) {
    int n = (argc > 1 ? atoi(argv[1]) : N);
    int m = (argc > 2 ? atoi(argv[2]) : 1<<20);

    clock_t start = clock();

    for (int i = 0; i < N; i++)
        clock();

    float duration = float(clock() - start) / CLOCKS_PER_SEC;
    printf("%.2fns\n", 1e9 * duration / N);

    return 0;
}
```

```c++
#include <bits/stdc++.h>

#ifndef N
#define N (1<<20)
#endif

void prepare(int *a, int n);
int lower_bound(int x);

int main(int argc, char* argv[]) {
    int n = (argc > 1 ? atoi(argv[1]) : N);
    int m = (argc > 2 ? atoi(argv[2]) : 1<<20);

    int *a = new int[n];
    int *q = new int[m];

    /*
    for (int i = 0; i < n; i++)
        a[i] = i;
    for (int i = 0; i < m; i++)
        q[i] = rand() % n;
    */

    for (int i = 0; i < n; i++)
        a[i] = rand();
    for (int i = 0; i < m; i++)
        q[i] = rand();

    a[0] = RAND_MAX;
    std::sort(a, a + n);

    prepare(a, n);

    int checksum = 0;
    clock_t start = clock();

    /*    
    for (int i = 0; i < m; i++) {
        int x = lower_bound(q[i]);
        int y = *std::lower_bound(a, a + n, q[i]);
        if (x != y) {
            std::cout << q[i] << " " << x << " " << y << std::endl;
            //for (int j = 0; j < n; j++)
            //    if (abs(a[j] - q[i]) <= 2)
            //        std::cout << a[j] << std::endl;
            //return 0;
        }
    }
    */

    /*
    int last = 0;

    for (int i = 0; i < m; i++) {
        last = lower_bound(q[i] ^ last);
        checksum ^= last;
    }
    */

    for (int i = 0; i < m; i++)
        checksum ^= lower_bound(q[i]);

    float seconds = float(clock() - start) / CLOCKS_PER_SEC;

    //printf("%.4f s total time\n", seconds);
    printf("%.2f ns per query\n", 1e9 * seconds / m);
    printf("%d\n", checksum);
    
    return 0;
}

```

Similarly in header files, e. g. for data structures that share the construction stage.

You might want to do something more complicated for performance-critical production code, but you are just prototyping, don't over-engineer it go with the simplest approach.

It is also helpful to include and either read from the standard input or (if you are multiple )


### Measuring the Right Thing

Also, make the dataset as representing of your real use case as possible, and reach an agreement with people on the procedure of benchmarking. This is especially important for data processing algorithms and data structures: most sorting algorithms perform differently depending on the input, hash tables perform differently with different distributions of keys.

Interleaving

Similar to how Americans report pre-tax salary, Americans use non-PPP-adjusted stats, attention-seeking startups report revenue instead of profit, performance engineers report the best version of benchmark if not stated otherwise.

I have never seen people do that though. It makes most difference when comparing branchy and branch-free algorithms.

```c++
for (int i = 0; i < m; i++)
    q[i] = rand();

int checksum = 0;

for (int i = 0; i < m; i++)
    checksum ^= lower_bound(q[i]);
```

```c++
for (int i = 0; i < m; i++)
    checksum ^= lower_bound(checksum ^ q[i]);
```

The best way to measure something is to plug it into real application.

You also may want to mark checksums as `volatile` to prevent the compiler from [optimizing too much](/hpc/cpu-cache/latency).

When your algorithm only writes data and doesn't calculate any sort of checksum, you can use `__sync_synchronize()`, which acts as a memory fence to prevent the compiler from optimizing between iterations.

People report things they like to report and leave out the things they don't.

Use random numbers. Not 1,2,3,4 because of branch prediction issues. You also better generate them ahead of time and use a fixed seed between invocations to minimize the noise and make the benchmark reproducible, which will help in debugging.

To put numbers in perspective, use statistics like "ns per query" or "cycles per byte" instead of wall clock whenever it is applicable. When you start to approach very high levels of performance, it makes sense to calculate what the theoretically maximal performance is and start thinking about your algorithm performance as a fraction of it.

### Noise Mitigation

Since we are guiding our optimization by experiments, it is important to account for side effects and external noise in them, especially when reporting results to someone else:

- Unless you are expecting a 2x kind of improvement, treat microbenchmarking the same way as A/B testing. When you run a program on a laptop for under a second, a ±5% fluctuation in performance is normal, so if you want to revert or keep a potential +1% improvement, run it until you reach a statistical significance, by calculating variances and p-values.
- Make sure there are no cold start effects due to cache. I usually solve this by making one cold test run where I check correctness of the algorithm, and then run it many times over for benchmarking (without checking correctness).
- If you benchmark a CPU-intensive algorithm, measure its performance in cycles using `perf stat`: this way it will be independent of clock frequency, fluctuations fo which is usually the main source of noise.
- Otherwise, set core frequency to the level you expect it to be and make sure nothing interferes with it. On Linux you can do it with `cpupower` (e. g. `sudo cpupower frequency-set -g powersave` to put it to minimum or `sudo cpupower frequency-set -g ondemand` to enable turbo boost). I use a [convenient GNOME shell extension](https://extensions.gnome.org/extension/1082/cpufreq/) that has a separate button to do it.

When running benchmarks, always quiesce the system:

- make sure no other jobs are running,
- turn turbo boost and hyper-threading off,
- turn off network and don't fiddle with the mouse,
- attach jobs to specific cores.

It is very easy to get skewed results without doing anything obviously wrong. Even a program's name can affect its speed: the executable's name ends up in an environment variable, environment variables end up on the call stack, and so the length of the name affects stack alignment, which can result in data accesses slowing down due to crossing cache line or memory page boundaries.

### Further Reading

In you are interested, you can explore this comprehensive [list of experimental computer science resources](https://www.cs.huji.ac.il/w~feit/exp/related.html) by Dror Feitelson, perhaps starting with "[Producing Wrong Data Without Doing Anything Obviously Wrong](http://eecs.northwestern.edu/~robby/courses/322-2013-spring/mytkowicz-wrong-data.pdf)" by Todd Mytkowicz et al.
