---
title: Getting Accurate Results
weight: 10
published: true
---

It is not an uncommon for there to be two library algorithm implementations, each maintaining its own benchmarking code, and each claiming to be faster than the other. This confuses everyone involved, especially the users, who have to somehow choose between the two.

Situations like these are usually not caused by fraudulent actions by their authors; they just have different definitions of what "faster" means, and indeed, defining and using just one performance metric is often very problematic.

### Measuring the Right Thing

There are many things that can introduce bias into benchmarks.

**Differing datasets.** There are many algorithms whose performance somehow depends on the dataset distribution. In order to define, for example, what the fastest sorting, shortest path, or binary search algorithms are, you have to fix the dataset on which the algorithm is run.

This sometimes applies even to algorithms that process a single piece of input. For example, it is not a good idea to feed GCD implementations sequential numbers because it makes branches very predictable:

```c++
// don't do this
int checksum = 0;

for (int a = 0; a < 1000; a++)
    for (int b = 0; b < 1000; b++)
        checksum ^= gcd(a, b);
```

However, if we sample these same numbers randomly, branch prediction becomes much harder, and the benchmark takes longer time, despite processing the same input, but in altered order:

```c++
int a[1000], b[1000];

for (int i = 0; i < 1000; i++)
    a[i] = rand() % 1000, b[i] = rand() % 1000;

int checksum = 0;

for (int t = 0; t < 1000; t++)
    for (int i = 0; i < 1000; i++)
        checksum += gcd(a[i], b[i]);
```


Although the most logical choices for most cases is to just sample data uniformly at random, many real-world applications have distributions that are far from uniform, so you can't pick just one. In general, a good benchmark should be application-specific, and use the dataset that is as representing of your real use case as possible.

<!--

People report things they like to report and leave out the things they don't.

To put numbers in perspective, use statistics like "ns per query" or "cycles per byte" instead of wall clock whenever it is applicable. When you start to approach very high levels of performance, it makes sense to calculate what the theoretically maximal performance is and start thinking about your algorithm performance as a fraction of it.

Similar to how Americans report pre-tax salary, Americans use non-PPP-adjusted stats, attention-seeking startups report revenue instead of profit, performance engineers report the best version of benchmark if not stated otherwise.


This happens especially often for data structures, and in general for algorithms whose performance somehow depends on the dataset distribution.

-->

**Multiple objectives.** Some algorithm design problems have more than one key objective. For example, hash tables, in addition to being highly dependant on the distribution of keys, also need to carefully balance:

- memory usage,
- latency of add query,
- latency of positive membership query,
- latency of negative membership query.

The only way to choose between hash table implementations is to try and put multiple variants into the application.

**Latency vs Throughput.** Another aspect that people often overlook is that the execution time can be defined in more than one way, even for a single query.

When you write code like this:

```c++
for (int i = 0; i < N; i++)
    q[i] = rand();

int checksum = 0;

for (int i = 0; i < N; i++)
    checksum ^= lower_bound(q[i]);
```

and then time the whole thing and divide it by the number of iterations, you are actually measuring the *throughput* of the query — how many operations it can process per unit of time. This is usually less than the time it actually takes to process one operation separately because of interleaving.

To measure actual *latency*, you need to introduce a dependency between the invocations:

```c++
for (int i = 0; i < N; i++)
    checksum ^= lower_bound(checksum ^ q[i]);
```

It usually makes the most difference in algorithms with possible pipeline stall issues, e.g., when comparing branchy and branch-free algorithms.

**Cold cache.** Another source of bias is the *cold cache effect*, when memory reads initially take longer time because the required data is not in cache yet.

This is solved by making a *warm-up run* before starting measurements:

```c++
// warm-up run

volatile checksum = 0;

for (int i = 0; i < N; i++)
    checksum ^= lower_bound(q[i]);


// actual run

clock_t start = clock();
checksum = 0;

for (int i = 0; i < N; i++)
    checksum ^= lower_bound(q[i]);
```

It is also sometimes convenient to combine the warm-up run with answer validation, if it is more complicated than just computing some sort of checksum.

**Over-optimization.** Sometimes the benchmark is outright erroneous because the compiler just optimized the benchmarked code away. To prevent the compiler from cutting corners, you need to add checksums and either print them somewhere or add the `volatile` qualifier, which also prevents any sort of interleaving of loop iterations.

For algorithms that only write data, you can use the `__sync_synchronize()` intrinsic to add a memory fence and prevent the compiler from accumulating updates.

### Reducing Noise

<!--

https://github.com/sosy-lab/benchexec

-->

The issues we've described produce *bias* in measurements: they consistently give advantage to one algorithm over the other. There are other types of possible problems with benchmarking that result in either unpredictable skews or just completely random noise, thus increasing *variance*.

These types of issues are caused by side effects and some sort of external noise, mostly due to noisy neighbors and CPU frequency scaling:

- If you benchmark a compute-bound algorithm, measure its performance in cycles using `perf stat`: this way it will be independent of clock frequency, fluctuations of which is usually the main source of noise.
- Otherwise, set core frequency to what you expect it to be and make sure nothing interferes with it. On Linux you can do it with `cpupower` (e.g., `sudo cpupower frequency-set -g powersave` to put it to minimum or `sudo cpupower frequency-set -g ondemand` to enable turbo boost). I use a [convenient GNOME shell extension](https://extensions.gnome.org/extension/1082/cpufreq/) that has a separate button to do it.
- If applicable, turn hyper-threading off and attach jobs to specific cores. Make sure no other jobs are running on the system, turn off networking and try not to fiddle with the mouse.

You can't remove noises and biases completely. Even a program's name can affect its speed: the executable's name ends up in an environment variable, environment variables end up on the call stack, and so the length of the name affects stack alignment, which can result in data accesses slowing down due to crossing cache line or memory page boundaries.

It is important to account for the noise when guiding optimizations and especially when reporting results to someone else. Unless you are expecting a 2x kind of improvement, treat all microbenchmarks the same way as A/B testing.

When you run a program on a laptop for under a second, a ±5% fluctuation in performance is completely normal. So, if you want to decide whether to revert or keep a potential +1% improvement, run it until you reach statistical significance, which you can determine by calculating variances and p-values.

### Further Reading

Interested readers can explore this comprehensive [list of experimental computer science resources](https://www.cs.huji.ac.il/w~feit/exp/related.html) by Dror Feitelson, perhaps starting with "[Producing Wrong Data Without Doing Anything Obviously Wrong](http://eecs.northwestern.edu/~robby/courses/322-2013-spring/mytkowicz-wrong-data.pdf)" by Todd Mytkowicz et al.

You can also watch [this great talk](https://www.youtube.com/watch?v=r-TLSBdHe1A) by Emery Berger on how to do statistically sound performance evaluation.
