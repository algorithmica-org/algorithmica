---
title: Reducing Tail Latency
weight: 7
published: true
---

In certain contexts, benchmarking can take a slightly different angle than the one discussed before. Namely, worst-case scenarios also need to be evaluated and brought under control. An example of such a context is a trading platform, where nanosecond-scale structure is sometimes a must, and even a rare jump several orders of magnitude in the high percentile may pose a risk, because the environment has already changed. There is, therefore, a need for a percentile benchmark.

### Read Time Stamp Counter

**Note**: This chapter focuses on x86-64 architecture. The techniques discussed (`RDTSC`, `LFENCE`, `RDTSCP`) are specific to x86 CPUs. Other architectures like ARM or RISC-V have different timing mechanisms and require alternative approaches.

The most intuitive way for the percentile benchmark would be to measure the time before the operation, the time after the operation, and subtract the former from the latter. This, however, is not an ideal solution, since getting the current time twice may have an overhead comparable to the running time of the measured operation itself. Because of that, it is advised to [batch the queries](/hpc/profiling/benchmarking) and compute the average duration for a batch.

It is possible, nevertheless, to measure the execution time on x86 platforms, thanks to [Read Time Stamp Counter](https://en.wikipedia.org/wiki/Time_Stamp_Counter) instruction. The instruction doesn't provide the exact execution time in regular human units. Instead, it accesses the cycle counter on the CPU and returns its current value. The measurement can still be done in a rather naive way:

```c++
uint64_t started_at = rdtsc();
// The work is done here.
uint64_t finished_at = rdtsc();
uint64_t duration_ticks = finished_at - started_at;
```

Historically, the instruction became available in 1993 on Pentium processors. The counter was physically a part of the computational unit itself, which had its consequences: since the CPU rate is volatile and can be affected by Turbo Boost as well as C-states and P-states, the rate of the counter had also been volatile. It was, however, often misused by programmers, who took the number of ticks and multiplied it by the base frequency of the processor; this way, neglecting the possible changes in power supply and eventual frequency change. This kind of counter was named **non-invariant** TSC.

With further developments, certain principles of work for the counter have changed: starting from Intel Core and AMD K8, the TSC rate has become constant, yet it was still stopping in the C-states. This modification gave rise to the **constant** TSC counters. The **invariant** counters were, in their turn, based on independent timekeeping hardware running at a constant frequency, and working with a constant rate in the P-, C-, and T-states.

Note that even with **invariant** TSC, synchronization across cores is not guaranteed by the CPU specification and depends on platform implementation. That means you need to make sure that you take both values in the measurement from the same CPU core.

This short historical detour implies that several considerations should be taken into mind by anyone who wants to start measuring the performance of a program:
- It makes sense to understand which exact kind of TSC is used in your CPU to be aware of possible problems that may affect precision. This is particularly important if you wish to convert your measurements from ticks to nanoseconds.
- Since certain implementations of TSC wouldn't guarantee you a synchronization across different cores, it makes sense to pin the execution in a way that both RDTSC calls are done within a single core. Not only will it allow you to avoid the discrepancies, but it will also be beneficial, since the program won't migrate from one core to another, which would result in a cold cache. On UNIX, you can do that with a `taskset` command, or, more granularly, with the `pthread_setaffinity_np` method.

Another, even more important consideration is the fact that the RDTSC instruction is not serializing, and therefore, can be reordered throughout the execution in order to speed it up. The reordering is evidently not what we're looking for, since the measured interval won't correspond to what one has initially specified in the code.

The issue can be addressed differently, and whatever the solution is, it makes sense to split the formerly mentioned `rdtsc` method into two: one for the start of the measurement, and one for its end. The measurement start must make sure that the instruction won't be executed earlier than it's supposed to. There are several ways to do that: for example, you can use the `CPUID` instruction, which is fully serializing.

Alternatively, you can use [`LFENCE`](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=3977,3977&text=lfence), which serializes only the loads, but has much smaller overhead. On modern Intel CPUs, `LFENCE` is also treated as a dispatch-serializing instruction, which makes it sufficient for ordering `RDTSC` in practice, despite its weaker architectural guarantees. Please note that the guarantees at AMD may not be as strong.

Apart from the CPU, it's also the compiler that could reorder some of the code instructions. The compiler barrier is used in the example code to avoid that.

```c++
uint64_t start_rdtsc() {
    // Prevent the compiler from moving the code of the measured part.
    asm volatile("" ::: "memory");

    // Make sure the load instructions up to this point are done.
    _mm_lfence();

    // Start measurement.
    uint64_t counter = __rdtsc();
    asm volatile("" ::: "memory");

    return counter;
}
```

The end of measurement is symmetric: you can use the [`RDTSCP`](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=3977,3977,5274&text=rdtscp), which waits for all previous instructions to complete execution before reading the timestamp, and follow it with `LFENCE` to prevent reordering of subsequent instructions.

```c++
uint64_t end_rdtsc() {
    // Prevent the compiler from moving the code of the measured part.
    asm volatile("" ::: "memory");

    // Contains processor ID; could be used to verify no core migration.
    uint32_t aux;

    // RDTSCP waits for all previous instructions to complete execution,
    // but does not wait for stores to be globally visible.
    // It is not a fully serializing instruction.
    uint64_t counter = __rdtscp(&aux);

    // LFENCE ensures subsequent loads don't execute before RDTSCP
    _mm_lfence();
    asm volatile("" ::: "memory");

    return counter;
}
```

Note that the intrinsics must be included. In many platforms, it's done by including `x86intrin.h`.

#### Converting TSC to Nanoseconds

The TSC ticks can be converted into the real-time units, first of all, if we talk about the **invariant TSC**, running with constant frequency. Please note that this frequency is often not the same as the frequency of the CPU itself. It can be deduced using several methods.

Certain systems allow you to get the rate from the `dmesg` command: `dmesg | grep -i tsc`. Note that the typical output would look like:

```
[    0.000000] tsc: Detected 2803.210 MHz processor
```

Meaning that the one second corresponds to $2803.210$ million TSC ticks.

Alternatively, you can calibrate against the time source. The code for that would look as follows:

```c++
uint64_t counter_at_start = start_rdtsc();
// Sleep or busy wait...
uint64_t counter_at_end = end_rdtsc();
```

The rate would then be a fraction of TSC ticks to the time interval. Once you have the rate, you can convert the ticks into the time units:

```c++
// TSC frequency for the test system (from dmesg or calibration)
constexpr double TSC_FREQ_GHZ = 2.803210;
double nanoseconds = ticks / TSC_FREQ_GHZ;
```

For the examples in this chapter, assuming the given TSC frequency:
- 26 ticks correspond to 9-10 nanoseconds;
- 983 ticks (p99.999 in the final measurement) correspond to approximately 350 nanoseconds.

### Toy Example: A Vector

Having the instrumentation in place, one can profile something. Perhaps, the easiest yet representative example would be the `push_back` operation in a `std::vector`. In a nutshell, this data structure allows for amortized $O(1)$ back insertions. However, _amortized_ doesn't mean it's always $O(1)$, and the new tool will help us to see that sometimes, when the capacity is exceeded, a simple operation takes tremendous amounts of time.

So we set the stage by creating a vector and adding one million elements to it. Along the way, we store the duration of each operation in the vector called `durations`:

```c++
std::vector<size_t> v;
for (size_t iter = 0; iter < 1'000'000; ++iter) {
    const uint64_t started_at = start_rdtsc();
    v.push_back(iter);
    const uint64_t finished_at = end_rdtsc();
    const uint64_t duration_ticks = finished_at - started_at;

    durations.emplace_back(duration_ticks, iter);
}
```

One can create a simple instrumentation around the `durations` vector, which we would leave as a simple exercise. Let's note that you need two principal sets of metrics:
- The values at certain percentiles: $50$, $75$, $85$, $95$, $99$, $99.9$, $99.99$, $99.999$. The first ones help to understand the behavior in a generic case, while the rest help to see the extremes and how fast the computation speed is saturated.
- The top-10 over the longest operations.

Once the instrumentation is in place, you can run the code and obtain the stats as follows.

```
Percentile 50: 26 TSC ticks
Percentile 75: 28 TSC ticks
Percentile 85: 43 TSC ticks
Percentile 95: 81 TSC ticks
Percentile 99: 89 TSC ticks
Percentile 99.9: 2531 TSC ticks
Percentile 99.99: 7466 TSC ticks
Percentile 99.999: 69159 TSC ticks
The longest iterations:
Iteration number=524288 Ticks=4493154
Iteration number=262144 Ticks=2445037
Iteration number=131072 Ticks=1567795
Iteration number=65536 Ticks=1454632
Iteration number=32768 Ticks=756793
Iteration number=16384 Ticks=464739
Iteration number=8192 Ticks=241878
Iteration number=13690 Ticks=114399
Iteration number=4096 Ticks=82943
Iteration number=53444 Ticks=69159
```

Please note that since the tests are done on regular hardware, many system events can intervene and create fluctuations. It's also a good practice to have some warmup runs or allow a fraction of the computation to serve this purpose. Still, the main points remain unchanged from run to run.

Two observations are evident. Even the $99.9$ percentile isn't what it's supposed to be: it's closer to the microsecond scale, rather than a nanosecond one, which demonstrates very well the amortized nature of the algorithm.

Secondly, the least robust operations are incidentally the powers of two. Of course, it's not a coincidence, since the vector allocates capacities in powers of two. So, when a power-of-two operation number arrives, the allocation and the values copying take place, resulting in a linear pass over all the elements of the vector, which is nowhere close to an actual, non-amortized $O(1)$.

Having identified the root cause of the problem, you can, of course, take the required precautions and reserve the required capacity in the vector. This way, no reallocations and copies will take place, and the structure moves closer to a "real", and not amortized, complexity.

```c++
std::vector<size_t> v;
v.reserve(1'000'000);
for (size_t iter = 0; iter < 1'000'000; ++iter) {
    // ...
}
```

The results are a little bit more reassuring, but still spark questions:

```
Percentile 50: 26 TSC ticks
Percentile 75: 48 TSC ticks
Percentile 85: 65 TSC ticks
Percentile 95: 85 TSC ticks
Percentile 99: 91 TSC ticks
Percentile 99.9: 2774 TSC ticks
Percentile 99.99: 8489 TSC ticks
Percentile 99.999: 43824 TSC ticks
The longest iterations:
Iteration number=123947 Ticks=331937
Iteration number=124369 Ticks=246069
Iteration number=39177 Ticks=145100
Iteration number=260110 Ticks=123364
Iteration number=192602 Ticks=97232
Iteration number=976382 Ticks=82628
Iteration number=101498 Ticks=56220
Iteration number=175645 Ticks=52483
Iteration number=21502 Ticks=46049
Iteration number=131523 Ticks=43824
```

First of all, the `reserve` has managed to shave off the worst scenarios: the new worst cases have an order of magnitude fewer TSC ticks per operation than before. Now, the worst-case asymptotic must be the _true_, non-amortized $O(1)$. Still, the higher percentiles are not convincing; the longest iterations no longer give a clear intuition about what happens in those worst cases.

The explanation here is that the test is done with a regular page size, which is 4 KB. When a structure reserves memory, it is not, in fact, allocated before a write to a new page is done. This write results in a page fault, and only then do most of the allocation routines actually happen. An idea comes to mind: what if we fault all those pages in advance, before the hot cycle, and perform the writes to the prepared memory? One way to do this would be:

```c++
std::vector<size_t> v;
v.resize(1'000'000);
v.clear();
for (size_t iter = 0; iter < 1'000'000; ++iter) {
    // ...
}
```

The results are more reassuring:

```c++
Percentile 50: 25 TSC ticks
Percentile 75: 28 TSC ticks
Percentile 85: 42 TSC ticks
Percentile 95: 69 TSC ticks
Percentile 99: 81 TSC ticks
Percentile 99.9: 85 TSC ticks
Percentile 99.99: 411 TSC ticks
Percentile 99.999: 12304 TSC ticks
The longest iterations:
Iteration number=26444 Ticks=89463
Iteration number=957100 Ticks=83958
Iteration number=60900 Ticks=58530
Iteration number=173952 Ticks=37688
Iteration number=458194 Ticks=28721
Iteration number=539786 Ticks=21515
Iteration number=818062 Ticks=21129
Iteration number=172694 Ticks=15442
Iteration number=456174 Ticks=12467
Iteration number=916779 Ticks=12304
```

Not only have the stats gone from six-digit durations to the five-digit ones in the tail outliers, but the high $99.9$ and $99.99$ percentiles have improved 20-30 times. Note that the percentiles could have also been reduced if [huge pages](/hpc/cpu-cache/paging/) were used, as fewer pages would have been needed, and fewer page faults would have happened.

The `push_back`, however, still has its overhead even for the pre-allocated scenario, which is clearly visible if you read the implementation of the method. To conclude the research on the matter, you can try to use a separate variable for the size and reimplement the back insertion, using the `std::vector` only as a holder for the allocated memory:

```c++
std::vector<size_t> v;
v.resize(1'000'000);
size_t v_size = 0;
for (size_t iter = 0; iter < 1'000'000; ++iter) {
    const uint64_t started_at = start_rdtsc();
    v[v_size++] = iter;
    const uint64_t finished_at = end_rdtsc();
    const uint64_t duration_ticks = finished_at - started_at;

    durations.emplace_back(duration_ticks, iter);
}
```

At this point, we've lost many of the conveniences that the vector gives: one needs to know the size in advance, there's a need to pre-allocate it, and there is no possibility to go beyond without tail latency losses. In addition, one should resize the vector back to the actual size once the hot loop is done. At this point, it would be much more beneficial to use other means if the tail latency is critical. Yet finally, we've tamed the $99.999$ percentile:

```
Percentile 50: 25 TSC ticks
Percentile 75: 27 TSC ticks
Percentile 85: 29 TSC ticks
Percentile 95: 45 TSC ticks
Percentile 99: 62 TSC ticks
Percentile 99.9: 67 TSC ticks
Percentile 99.99: 404 TSC ticks
Percentile 99.999: 983 TSC ticks
The longest iterations:
Iteration number=80416 Ticks=83473
Iteration number=8582 Ticks=68766
Iteration number=241688 Ticks=31947
Iteration number=551329 Ticks=29025
Iteration number=948282 Ticks=22123
Iteration number=197102 Ticks=16396
Iteration number=27422 Ticks=4309
Iteration number=293886 Ticks=1071
Iteration number=254462 Ticks=989
Iteration number=8702 Ticks=983
```

### Dealing with Jitter

All experiments from the example above were run on a regular laptop, having, at the same time, the regular applications and system services. This setup inevitably has lots of things that can intervene, and therefore, contribute to the worst case samples:

1. The context switches are possible, although they aren't a big problem in the context of benchmarking the code. Overall, the execution is rather quick and is under one second, so the process is not very likely to be interrupted in between. A context switch, however, will definitely create a data entry for the tail outlier list. To mitigate that, you can extract the run metrics from `perf stat` and make sure that no context switch took place, and otherwise omit the measurements.
2. In the more complex algorithms, the first iterations might be slow due to a cold cache; it's recommended, therefore, to adopt a cache warming strategy.
3. The Turbo Boost, C-states, and P-states may affect the basic metrics. It is advised to turn them off, if possible. You need to also make sure you follow the advice given in a different chapter of the book.
4. The OS and hardware interruptions are therefore a main reason for the tail latency jumps in the extremes. The real production servers solve this problem by forbidding the OS to use certain cores, pinning execution threads to cores, and using the `isolcpus` kernel parameter. In a more simplified setup, such as a personal laptop, it can only be advised not to have too many running processes at the time of the microbenchmark.
5. SMT and Hyper-Threading can also introduce variability: when two threads share the same physical core, they compete for execution resources. For truly stable measurements, consider disabling hyperthreading or ensuring your thread runs on a physical core without a sibling thread active. This can be controlled via CPU affinity and `lscpu` to map logical to physical cores.
