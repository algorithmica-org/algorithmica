---
title: Statistical Profiling
weight: 2
---

[Instrumentation](../instrumentation) is a rather tedious way of doing profiling, especially if you are interested in multiple small sections of the program. And even if it can be partially automated by the tooling, it still won't help you gather some fine-grained statistics because of its inherent overhead.

Another, less invasive approach to profiling is to interrupt the execution of a program at random intervals and look where the instruction pointer is. The number of times the pointer stopped in each function's block would be roughly proportional to the total time spent executing these functions. You can also get some other useful information this way, like finding out which functions are called by which functions by inspecting [the call stack](/hpc/architecture/functions).

This could, in principle, be done by just running a program with `gdb` and `ctrl+c`'ing it at random intervals but modern CPUs and operating systems provide special utilities for this type of profiling.

### Hardware Events

Hardware *performance counters* are special registers built into microprocessors that can store the counts of certain hardware-related activities. They are cheap to add on a microchip, as they are basically just binary counters with an activation wire connected to them.

Each performance counter is connected to a large subset of circuitry and can be configured to be incremented on a particular hardware event, such as a branch mispredict or a cache miss. You can reset a counter at the start of a program, run it, and output its stored value at the end, and it will be equal to the exact number of times a certain event has been triggered throughout the execution.

You can also keep track of multiple events by multiplexing between them, that is, stopping the program in even intervals and reconfiguring the counters. The result in this case will not be exact, but a statistical approximation. One nuance here is that its accuracy can’t be improved by simply increasing the sampling frequency because it would affect the performance too much and thus skew the distribution, so to collect multiple statistics, you would need to run the program for longer periods of time.

Overall, event-driven statistical profiling is usually the most effective and easy way to diagnose performance issues.

### Profiling with perf

Performance analysis tools that rely on the event sampling techniques described above are called *statistical profilers*. There are many of them, but the one we will mainly use in this book is [perf](https://perf.wiki.kernel.org/), which is a statistical profiler shipped with the Linux kernel. On non-Linux systems, you can use [VTune](https://software.intel.com/content/www/us/en/develop/tools/oneapi/components/vtune-profiler.html#gs.cuc0ks) from Intel, which provides roughly the same functionality for our purposes. It is available for free, although it is proprietary, and you need to refresh your community license every 90 days, while perf is free as in freedom.

Perf is a command-line application that generates reports based on the live execution of programs. It does not need the source and can profile a very wide range of applications, even those that involve multiple processes and interaction with the operating system.

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

After compiling it (`g++ -O3 -march=native example.cc -o run`), we can run it with `perf stat ./run`, which outputs the counts of basic performance events during its execution:

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

You can see that the execution took 0.53 seconds or 852M cycles at an effective 1.32 GHz clock rate, over which 479M instructions were executed. There were also 122.7M branches, and 15.7% of them were mispredicted.

You can get a list of all supported events with `perf list`, and then specify a list of specific events you want with the `-e` option. For example, for diagnosing binary search, we mostly care about cache misses:

```yaml
> perf stat -e cache-references,cache-misses ./run

91,002,054      cache-references:u                                          
44,991,746      cache-misses:u      # 49.440 % of all cache refs
```

By itself, `perf stat` simply sets up performance counters for the whole program. It can tell you the total number of branch mispredictions, but it won't tell you *where* they are happening, let alone *why* they are happening.

To try the stop-the-world approach we discussed previously, we need to use `perf record <cmd>`, which records profiling data and dumps it as a `perf.data` file, and then call `perf report` to inspect it. I highly advise you to go and try it yourselves because the last command is interactive and colorful, but for those that can't do it right now, I'll try to describe it the best I can.

When you call `perf report`, it first displays a `top`-like interactive report that tells you which functions are taking how much time:

```
Overhead  Command  Shared Object        Symbol
  63.08%  run      run                  [.] query
  24.98%  run      run                  [.] std::__introsort_loop<...>
   5.02%  run      libc-2.33.so         [.] __random
   3.43%  run      run                  [.] setup
   1.95%  run      libc-2.33.so         [.] __random_r
   0.80%  run      libc-2.33.so         [.] rand
```

Note that, for each function, just its *overhead* is listed and not the total running time (e.g., `setup` includes `std::__introsort_loop` but only its own overhead is accounted as 3.43%). There are tools for constructing [flame graphs](https://www.brendangregg.com/flamegraphs.html) out of perf reports to make them more clear. You also need to account for possible inlining, which is apparently what happened with `std::lower_bound` here. Perf also tracks shared libraries (like `libc`) and, in general, any other spawned processes: if you want, you can launch a web browser with perf and see what's happening inside.

Next, you can "zoom in" on any of these functions, and, among others things, it will offer to show you its disassembly with an associated heatmap. For example, here is the assembly for `query`:

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

On the left column is the fraction of times that the instruction pointer stopped on a specific line. You can see that we spend ~65% of the time on the jump instruction because it has a comparison operator before it, indicating that the control flow waits there for this comparison to be decided.

Because of intricacies such as [pipelining](/hpc/pipelining) and out-of-order execution, "now" is not a well-defined concept in modern CPUs, so the data is slightly inaccurate as the instruction pointer drifts a little bit forward. The instruction-level data is still useful, but at the individual cycle level, we need to switch to [something more precise](../simulation).

<!-- flame graphs -->
