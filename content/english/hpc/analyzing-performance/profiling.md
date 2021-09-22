---
title: Profiling and Benchmarking
weight: 4
---

There are two general ways of finding performance issues: starting at the code and profiling. Just as there are three levels of depth in the first approach — you can inspect source code, immediate representation and assembly — there are three main approaches when it comes to profiling: instrumentation, statistical profiling and simulation.

## Instrumentation

Instrumentation is an overcomplicated term that means inserting timers and other tracking code into programs. The simplest example is using the `time` utility in Unix-like systems to measure the duration of execution for the whole program.

More generally, you want to know *which parts* of the program actually need optimizaiton. There are tools shipped with compilers and IDEs that can time designated functions automatically, but it is more robust to do it by hand using any methods of interacting with time the language provides:

```cpp
clock_t start = clock();
do_something();
float seconds = float(clock() - start) / CLOCKS_PER_SEC;
printf("do_something() took %.4f", seconds);
```

One nuance here is that you can't measure the execution time of particularly quick functions this way. The `clock` function returns time in microseconds ($10^{-6}$), and it does so by waiting to the nearest ceiled microsecond, so it basically takes up to 1000ns to complete, which is an ethernity in the world of low-level optimization.

As a workaround, you can invoke the function repeatedly in a loop, time the whole thing once and divide the total time by the number of iterations. You also need to ensure nothing gets cached and there are no similar side effects. That's a quite tedious in my opinion, especially if you are interested in multiple small sections of the program.

### Sampling

Instrumentation can also be used to collect other types of info that can give us useful insights about a particular algorithm. For example:

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

Mathematically, what we are doing here is repeatedly sampling from [Bernoulli distribution](https://en.wikipedia.org/wiki/Bernoulli_distribution) (with $p$ equal to sample rate) until we get a seccess. There is another distribution that tells us how many iterations of Bernoulli sampling we need to get a positive, called [geometric distribution](https://en.wikipedia.org/wiki/Geometric_distribution). What we can do is to sample from it instead and use that value as a decrementing counter:

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

## Statistical Profiling

Another, less invasive approach to profiling is to interrupt the execution of a program at random intervals and look where the instruction pointer is: the number of times the pointer stopped in each function's block is roughly proportional to the total time spent executing these functions. You can also get some other useful information this way, like finding out which functions are called by which functions by inspecting the call stack.

This could in principle be done by just running a program with `gdb` and `ctrl+c`'ing it at random intervals, but operating systems and modern CPUs provide special utilities for this type of profiling. Hardware *performance counters* are special registers built into microprocessors that can store the counts of certain hardware-related activities. They are cheap to add to CPUs, as they are basically just binary counters with an activation wire connected to them.

Each performance counter is connected to a large subset of circuitry and can be configured to be incremented on a particular hardware event, like a branch mispredict or a cache miss. You can simply reset a counter at the start of a program and output its stored value at the end, and it will be equal to the exact number of times a certain event has been triggered.

You can also keep track of multiple events by *multiplexing* between them, that is, stopping the program and reconfiguring counters in even intervals. The result in this case will not be exact, but a statistical approximation. One nuance here is that its accuracy can't be improved by simply increasing the frequency of sampling, because it would affect the performance too much and thus skew the distribution.

Overall, event-driven statistical profiling is usually the most effective and easy way to diagnose performance issues.

### Profiling with perf

There are many profilers and other performance analyzing tools. The tool we will mostly rely on in this book is [perf](https://perf.wiki.kernel.org/), which is a statistical profiler available in the Linux kernel. On non-Linux systems, you can use VTune from Intel, which provides roughly the same functionality for our purposes. It is available for free, although it is a proprietary software for which you need to refresh a community license every 90 days, while perf is free as in freedom.

Perf is a command-line application that generates reports based on live execution of programs. It does not need the source and can profile a very wide range of applications, even those that involve multiple processes and interaction with the operating system.

For explanation purposes, I have written a small program that creates an array of a million random integers, sorts it, and then does a million binary searches on it:

```c++
void setup() {
    for (int i = 0; i < n; i++)
        a[i] = rand();
    std::sort(a, a + n);
}

int query() {
    int checksum = 0;
    for (int i = 0; i < n; i++) {
        int idx = std::lower_bound(a, a + n, rand()) - a;
        checksum += idx;
    }
    return checksum;
}
```

After compiling it (`g++ -O3 -march=native example.cc -o run`), we can run it with `perf stat ./run`, which output the counts of basic performance events during the execution:

```yaml
 Performance counter stats for './run':

        646.07 msec task-clock:u               # 0.997 CPUs utilized          
             0      context-switches:u         # 0.000 K/sec                  
             0      cpu-migrations:u           # 0.000 K/sec                  
         1,096      page-faults:u              # 0.002 M/sec                  
   852,125,255      cycles:u                   # 1.319 GHz (83.35%)
    28,475,954      stalled-cycles-frontend:u  # 3.34% frontend cycles idle (83.30%)
    10,460,937      stalled-cycles-backend:u   # 1.23% backend cycles idle (83.28%)
   479,175,388      instructions:u             # 0.56  insn per cycle         
                                               # 0.06  stalled cycles per insn (83.28%)
   122,705,572      branches:u                 # 189.925 M/sec (83.32%)
    19,229,451      branch-misses:u            # 15.67% of all branches (83.47%)

   0.647801770 seconds time elapsed
   0.647278000 seconds user
   0.000000000 seconds sys
```

You can see that the execution took 0.53 seconds, or 852M cycles at effective 1.32 GHz clock rate, over which 479M instructions were executed. There was also a total of 122.7M branches, and 15.7% of them were mispredicted.

You can get a list of all supported events with `perf list`, and then specify a concrete list of events you want with the `-e` option. For example, for diagnosing binary search, we mostly care about cache misses:

```yaml
> perf stat -e cache-references,cache-misses ./run

91,002,054      cache-references:u                                          
44,991,746      cache-misses:u      # 49.440 % of all cache refs
```

By itself, `perf stat` tells you the total number of branch mispredicts, but it won't tell you *where* they are happening, let alone *why* they are happening. It simply sets up performance counters for the whole program.

To try the stop-the-world approach we talked about initially, we need to use `perf record <cmd>`, which records profiling data and dumps it as a `perf.data` file, and then `perf report` to inspect it. I highly advise you to go and try it yourselves, because the last command is interactive and colorfull, but for those that can't do it right now I'll try to describe it the best I can.

When you call `perf report`, it first displays a `top`-like interactive report which will tells you which functions are taking how much time:

```
Overhead  Command  Shared Object        Symbol
  63.08%  run      run                  [.] query
  24.98%  run      run                  [.] std::__introsort_loop<...>
   5.02%  run      libc-2.33.so         [.] __random
   3.43%  run      run                  [.] setup
   1.95%  run      libc-2.33.so         [.] __random_r
   0.80%  run      libc-2.33.so         [.] rand
```

Note that, for each function, just its *overhead* is listed and not the total running time (e. g. `setup` includes `std::__introsort_loop` but only its own overhead is accounted as 3.43%). You also need to account for possible inlining, which is apparently the case here for `std::lower_bound`. Note that it also tracks shared libraries, and, in general, any other spawned processes: you can launch a web browser with perf and see what's happening inside.

Next, you can "zoom in" on each of these functions, and, among others things, it will offer to show you its disassembly with an associated heatmap. Here is the assembly for `query`:

```asm
       │20: → call   rand@plt
       │      mov    %r12,%rsi
       │      mov    %eax,%edi
       │      mov    $0xf4240,%eax
       │      nop    
       │30:   test   %rax,%rax
  4.57 │    ↓ jle    52
       │35:   mov    %rax,%rdx
  0.52 │      sar    %rdx
  0.33 │      lea    (%rsi,%rdx,4),%rcx
  4.30 │      cmp    (%rcx),%edi
 65.39 │    ↓ jle    b0
  0.07 │      sub    %rdx,%rax
  9.32 │      lea    0x4(%rcx),%rsi
  0.06 │      dec    %rax
  1.37 │      test   %rax,%rax
  1.11 │    ↑ jg     35
       │52:   sub    %r12,%rsi
  2.22 │      sar    $0x2,%rsi
  0.33 │      add    %esi,%ebp
  0.20 │      dec    %ebx
       │    ↑ jne    20
```

On the left you can see the fraction of times the instuciton pointer stopped on a specific line. Because of pipelining and out-of-order execution, "now" is not a well defined concept, so the data is slightly inaccurate as the instruction pointer drifts a little bit forward. But it is still useful: here we spend ~65% of the time on the jump instruction because if has a comparison operator before it, indicating that he control flow waits there for this comparison to be decided.

At the individual cycle level we need something more precise.

## Simulation

The last approach (or rather a group of them) is not to gather the data by actually running the program, but to analyze what should happen by simulating it with a specialized tools, which roughly fall in two categories.

The first one is memory profilers. A particular example is `cachegrind`, which is a part of `valgrind`. It simulates all memory operations to assess memory performance, although usually significantly slowing down the program in the process. They can usually be replaced with `perf` cache events though.

The second category is machine code analyzers. These are programs that take assembly code and simulate its execution on a particular microarchitecture using information available to compilers, and output the latency and throughput of the whole snippet, as well as cycle-perfect utilizaiton of various resources in a CPU.

There are many of them, but I personally prefer `llvm-mca`, which you can probably install via a package manager together with clang. You can also access it through a new web-based tool called [UICA](https://uica.uops.info).

What it does is it runs a set number of iterations of a given snippet and computes statistics about resource usage of each instruction, which is useful for finding out where the bottleneck is. Here is an example of its analysis of an array sum on Skylake — you are not going to understand much, but that's fine for now:

```yaml
Iterations:        100
Instructions:      400
Total Cycles:      108
Total uOps:        500

Dispatch Width:    6
uOps Per Cycle:    4.63
IPC:               3.70
Block RThroughput: 0.8
```

First, it outputs general information about the loop and the hardware:

- It "ran" it 100 times, executing 400 instructions in total in 108 cycles, which is the same as executing $\frac{400}{108} \approx 3.7$ instructions per cycle ("IPC") on average.
- The CPU is theoretically capable of executing up to 6 instructions per cycle ("dispatch width"). In reality this is much more complicated, but in essense, there are several "ports" that specialize on particular kinds of instructions, which often become the bottleneck.
- Each cycle in theory can be executed in 0.8 cycles on average ("block reciprocal throughput").
- The "uOps" here are the micro-operations that CPU splits each instruction into (e. g. fused load-add is composed of two uOps). We will talk about them in detail, but much later.

Then it proceeds to give information about each individual instruction: 

```yaml
Instruction Info:
[1]: uOps
[2]: Latency
[3]: RThroughput
[4]: MayLoad
[5]: MayStore
[6]: HasSideEffects (U)

[1]    [2]    [3]    [4]    [5]    [6]    Instructions:
 2      6     0.50    *                   addl	(%rax), %edx
 1      1     0.25                        addq	$4, %rax
 1      1     0.25                        cmpq	%rcx, %rax
 1      1     0.50                        jne	-11
```

There is nothing there that there isn't in the instruction tables:

- How many uOps each instruciton is split into.
- How many cycles each instruction takes to complete ("latency").
- How many cycles each instruction takes to complete in the amortized sense ("reciprocal throughput"), considering that several copies of it can be executed simultaneously.

Then it outputs probably the most important part — which instructions are executing when and where:

```yaml
Resource pressure by instruction:
[0]    [1]    [2]    [3]    [4]    [5]    [6]    [7]    [8]    [9]    Instructions:
 -      -     0.01   0.98   0.50   0.50    -      -     0.01    -     addl (%rax), %edx
 -      -      -      -      -      -      -     0.01   0.99    -     addq $4, %rax
 -      -      -     0.01    -      -      -     0.99    -      -     cmpq %rcx, %rax
 -      -     0.99    -      -      -      -      -     0.01    -     jne  -11
```

A CPU is a very complicated thing, so it outputs a lot of information. We are not ready to discuss it in detail yet, but we will in the last chapter.

## Algorithm Design as an Empirical Field

(This section is a draft.)

I like to think about these three profiling methods by an analogy of how natural scientists study small things, picking the right tool based on the required level of precision:

- When objects are on a micrometer scale, they use optical microscopes. (`time`, `perf stat`, instrumentation)
- When objects are on a nanometer scale and light no longer interacts with them, they use electron microscopes. (`perf record` / `perf report`, heatmaps)
- When objects are smaller than that (i. e. to peek inside of an atom), they resort to theories and assumptions about how things work. (`llvm-mca`, `cachegrind`, staring at assembly)

For practical algorithm design, we use the same empirical methods, although this is not because we don't know some of the secrets of nature, but mostly because modern computers are too complex to analyze — although this is also true that we, regular software engineers, can't know some of the details because of IP protection from hardware companies. In fact, considering that most accurate x86 instruction tables are [reverse-engineered](https://arxiv.org/pdf/1810.04610.pdf), there is a reason to believe that Intel doesn't know these details themselves.

### Managing Experiments

If you do it correctly, working on improving performance should resemble a loop:

1. run the program and collect metrics,
2. figure out where the bottleneck is,
3. remove the bottleneck and go to step 1.

The shorter this loop is, the faster you will iterate. Here are some hints on how to set up your environment to achieve this (you can find many examples in the [code repo](https://github.com/sslotin/ahm-code) for this book):

- Separate all testing and analytics code from the implementation of the algorithm itself, and also different implementations from each other. In C/C++, you can do this by creating a single header file (e. g. `matmul.hh`) with a function interface and the code for its benchmarking in `main`, and many implementation files for each algorithm version (`v1.cc`, `v2.cc`, etc.) that all include that single header file.
- To speed up builds and reruns, create a Makefile or just a bunch of small scripts that also calculate the statistics you may need.
- To speed up high-level analytics, create a Jupyter notebook where you put small scripts and do all the plots. You can also put build scripts there if you feel like it.
- To put numbers in perspective, use statistics like "ns per query" or "cycles per byte" instead of wall clock. When you start to approach very high levels of performance, it makes sense to calculate what the theoretically maximal performance is and start thinking about your algorithm performance as a fraction of it.

Make the dataset as representing of your real use case as possible, and reach an agreement with people upon the procedure of benchmarking. This is especially important for data structures. Most sorting algorithms perform differently depending on the input. Hash tables perform differently with different distributions of keys.

### Removing Noise

Since we are guiding our optimization by experiments, it is important to account for side effects and external noise on them, especially when reporting results to someone else:

- Unless you are expecting a 2x kind of improvement, treat microbenchmarking the same way as A/B testing. When you run a program on a laptop for under a second, a ±5% fluctiation in performance is normal, so if you want to revert or keep a potential +1% improvement, run it until you reach a statistical significance, by calculating variances and p-values.
- Make sure there are no cold start effects due to cache. I usually solve this by making one cold test run where I check correctness of the algorithm, and then run it many times over for benchmarking.
- If you benchmark a CPU-intensive algorithm, measure its performance in cycles using `perf stat`: this way it will be independent of clock frequency, which is usually the main source of noise.
- Otherwise, set core frequency to the level you expect it to be and make sure nothing interferes with it. On linux you can do it with `cpupower` (e. g. `sudo cpupower frequency-set -g powersave` to put it to minimum or `sudo cpupower frequency-set -g ondemand` to enable turbo boost).

It is very easy to get skewed results without doing anything obviously wrong. It is also important to quiesce the system:

- make sure no other jobs are running,
- turn turbo boost and hyperthreading off,
- turn off network and don't fiddle with the mouse,
- tttach jobs to specific cores.

Even a program's name can affect its speed: the executable's name ends up in an environment variable, environment variables end up on the call stack, and the length of the name will affect stack allignment, and data access can slow down when crossing cache line of page boundaries.
