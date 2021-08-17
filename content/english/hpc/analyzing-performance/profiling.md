---
title: Profiling and Benchmarking
weight: 4
---

There are two general ways of finding performance issues: starting at the code and profiling. Just as there are 3 levels of depth in the first approach — you can inspect source code, immediate representation and assembly — there are 3 main approaches when it comes to profiling.

## Instrumentation

Instrumentation is an overcomplicated term that means inserting timers into functions.

The simplest example is using the `time` utility in Unix-like systems to measure the duration of execution for the whole program.

More generally, you want to know *which parts* of the program actually need optimizaiton. There are tools shipped with compilers and IDEs that can time designated functions automatically, but it is more robust to do it by hand using any of the built-in methods to interact with time:

```c++
clock_t start = clock();
do_something();
float seconds = float(clock() - start) / CLOCKS_PER_SEC;
printf("do_something() took %.4f", seconds);
```

The main disadvantage of this method is that the `clock` function takes around 1000ns, which is an ethernity in the world of low-level optimization. You can't time especially quick procedures this way, although as a workaround you can invoke it repeatedly in a loop, ensure nothing gets cached, time the whole thing once, and divide the total time by the number of iterations; but that's way too much work in my opinion, especially if you are interested in multiple small sections of the program.

Instrumentation can also be used to collect other types of info that can give us useful insights about a particular algorithm. For example, when designing a hash function, we are interested in the average length of its input; for a binary tree, we care about its size and height; and for a sorting algorithm, we we want to know how many comparisons it does. In a similar way, we can insert counters in the code that calculate these algorithm-specific statistics.

### Sampling

Adding counters has the disadvantage of introducing overhead, although you can mitigate it almost completely by only doing it randomly for a small fraction of invocations:

```c++
void query() {
    if (rand() % 100 == 0) {
        // update statistics
    }
    // main logic
}
```

If the sample rate is small enough, the only remaining overhead per invocation will be random number generation and a condition check. Interestingly, we can optimize it a little bit with some stats magic.

Mathematically, what we are doing here is sampling from [Bernoulli distribution](https://en.wikipedia.org/wiki/Bernoulli_distribution) (with $p$ equal to sample rate) repeatedly until we get a seccess. There is another distribution that tells us how many iterations of Bernoulli sampling we may need, called [geometric distribution](https://en.wikipedia.org/wiki/Geometric_distribution). What we can do is to sample from it instead and use that value as a decrementing counter:

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

Another, less invasive approach to profiling is to interrupt the execution of a program at random intervals and look where the instruction pointer is: the number of times the pointer stopped in each function's block is roughly proportional to the total time spent executing these functions.

You can get more information by inspecting the call stack. Like which functions are calling which procedures.

This could in principle be done by just running a program with `gdb` and `ctrl+c`'ing it at random intervals, but operating systems and modern CPUs provide special utilities for this type of profiling.

Hardware *performance counters* are special registers built into microprocessors that can store the counts of certain hardware-related activities. They are cheap to add to CPUs, as they are basically just binary counters with an activation wire connected to them. Each performance counter is connected to a large subset of circuitry and can be set to increment on a particular hardware event, like a branch mispredict or a cache miss.

One nuance here is that the resulting data is not exact, but a statistical approximation. More over, you can't fully resolve it by simply increasing the frequency of sampling, because it would affect the performance too much and skew the distribution. But overall, this is usually the most effective and easy way to diagnose performance issues.

## Simulation

The last approach (or rather a group of them) is to gather the data not by actually running the program, but to analyze what happens by simulating it with a specialized tool.

One such example is `cachegrind`, which is a memory profiler and a part of `valgrind`. It simulates all memory operations to assess memory performance, although usually significantly slowing down the program in the process.

Another is `llvm-mca`, which we will cover later in the book. It is a program that takes assembly code and simulates its execution on a particular microarchitecture using information available to compilers, and outputs its latency and throughput, as well as cycle-perfect utilizaiton of various resources in a CPU.

## Quiescing the System

It is very easy to get skewed results without doing anything obviously wrong. Here is a (non-extensive) checklist of what to do before measuring performance:

- Make sure no other jobs are running.
- Turn turbo boost and hyperthreading off.
- Turn off network and don't fiddle with the mouse.
- Attach jobs to specific cores.

Even a program's name can affect its speed: the executable's name ends up in an environment variable, environment variables end up on the call stack, and the length of the name will affect stack allignment, and data access can slow down when crossing cache line of page boundaries.

## Profiling with `perf`

There are many profilers and other performance analyzing tools. The tool we will mostly rely on in this book is `perf`, which is a statistical profiler available in Linux kernel. On non-Linux systems, you can use VTune from Intel, which provides roughly the same functionality for our purposes. It is available for free, although it is proprietary software for which you need to refresh a community license every 90 days, while `perf` is free as in freedom.

Perf is a command-line application that generates reports based on live execution of programs. It does not need the source and can profile a very wide range of applications, even those that involve multiple processes and interaction with the operating system.

For explanation purposes, I've written a small program that creates an array of a million random integers, sorts it, and then does a million binary searches on it:

```c++
void setup() {
    for (int i = 0; i < n; i++)
        a[i] = rand();
    sort(a, a + n);
}

int query() {
    int checksum = 0;
    for (int i = 0; i < n; i++) {
        int idx = lower_bound(a, a + n, rand()) - a;
        checksum += idx;
    }
    return checksum;
}
```

Ignoring all the things I've just said about quiescing the system,

After compiling it (`g++ -O3 -march=native example.cc -o run`), we can run it with `perf stat ./run`, which will count performance events:

```bash
 Performance counter stats for './run':

            646.07 msec task-clock:u              #    0.997 CPUs utilized          
                 0      context-switches:u        #    0.000 K/sec                  
                 0      cpu-migrations:u          #    0.000 K/sec                  
             1,096      page-faults:u             #    0.002 M/sec                  
       852,125,255      cycles:u                  #    1.319 GHz                      (83.35%)
        28,475,954      stalled-cycles-frontend:u #    3.34% frontend cycles idle     (83.30%)
        10,460,937      stalled-cycles-backend:u  #    1.23% backend cycles idle      (83.28%)
       479,175,388      instructions:u            #    0.56  insn per cycle         
                                                  #    0.06  stalled cycles per insn  (83.28%)
       122,705,572      branches:u                #  189.925 M/sec                    (83.32%)
        19,229,451      branch-misses:u           #   15.67% of all branches          (83.47%)

       0.647801770 seconds time elapsed

       0.647278000 seconds user
       0.000000000 seconds sys
```

You can see that the execution took 852M cycles, over which 479M instructions were executed.

You can see here that it has 122.7M branches, and 15.6% of them were mispredicted.

You can also specify a concrete list of events you want with `-e` option. You can get a list of supported events with `perf list`. But don't include too many:

`perf stat -e cache-references,cache-misses ./run`

```
91,002,054      cache-references:u                                          
44,991,746      cache-misses:u            #   49.440 % of all cache refs
```

`perf stat` doesn't do any actual profiling. It just sets up performance counters.

`perf record` and `perf report`. I highly advise to go and try it yourselves, because these commands are interactive, but I'll describe it as well as I can.

`perf.data`.

It will display a `top`-like interactive report which will tell 

```
Overhead  Command  Shared Object        Symbol
  63.08%  run      run                  [.] query
  24.98%  run      run                  [.] std::__introsort_loop<...>
   5.02%  run      libc-2.33.so         [.] __random
   3.43%  run      run                  [.] setup
   1.95%  run      libc-2.33.so         [.] __random_r
   0.80%  run      libc-2.33.so         [.] rand
```

(`std::lower_bound` apparently was inlined)

You can "zoom in" on each of them and it will show you a heatmap and many other cool features. It also spends almost 8% of the time generating random numbers.

It is not very reliable.

```bash
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

At this level, it's better to switch to brain or simulators. It is sort of similar to inability to use optical microscope to measure objects lower than wavelength.

Because of out-of-order execution, "now" is not a well defined concept.

Because computers don't really work like that, it will drift a little bit forward.

Here it spends 65% of the time (as a fraction of what was sampled in `query`) on the jump instruction because if hase a comparison operator before it. It just waits on the operation that it can't decide.

---

This is similar to how natiral scientists study small things.

Optical microscopes, Electron microscope, and then resort to theories and exact assumption of how things work.

Microscopes may figure out its size, but they can't peek *inside* an atom.

You change tools, from using generic instrumentation-based profiling, to events-based and statistical ones, to using brain and exact simulated models of things are supposed to work.

It tells you the total number of branch mispredicts, but it won't tell you *where* they are happening, let alone *why* they are happening.

---

### Algorithm Design is an Empirical Field

I came from a non-performance field. A lot of people in scientific computing do. Computational biology, fluid dynamics, graphics... Only a handful of us develop compilers, databases and map-reduce systems. or other "pure software".

Leaving aside that some details in Intel documentations are actually reverse-engineered and have comparable complexity with quantuum mechanics, algorithm design is an empirical field too.

I came to machine learning because it took the empirical approach from physics and other natural sciences and methods from computer science.

Modern algorithm design is an empirical field too. But it is limited not by unknowns, but by our lack of understanding computers.

Maybe there is someone who knows all the rules, but it doesn't change the reality for us. We still have partial information, and it doesn't really matter why.


For people who don't use tools and are learning towards skipping this section. I don't generally use a debugger myself.

There are three groups of people: those who use debuggers, those who don't but feel that they are bad programmers for that, and those that don't use it consciously.

When I'm just learning the language or a library. Or resort to printing, whichever seems less work-intensive.

There are numerous people who don't use a debugger. Guido van Rossum never had and at this point probably never will stop using prints. You can find quite a few obscene Linus Torvalds emails with his thoughts on kernel debugger. The only motivation for that is that you have limited time, and sometimes it is better spent on trying to understand program better rather than watching it crash in slow motion. It is a bug, so there must be a line responsible for it. If you can't find it in a reasonable time (which is very small if you have tests), then you can do debugging, but this should be really rare in properly written software.

Profiling is very different. You don't simply have a single-line *bug* that affects your performance. It involves a much higher level of interaction, on the algorithm level.

Debugging is useful in cases where you don't know the language.

But profiling is different. It is always for cases when you don't know what's happening.
