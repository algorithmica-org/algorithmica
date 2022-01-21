---
title: Benchmarking
weight: 6
---

Also, make the dataset as representing of your real use case as possible, and reach an agreement with people on the procedure of benchmarking. This is especially important for data processing algorithms and data structures: most sorting algorithms perform differently depending on the input, hash tables perform differently with different distributions of keys.

https://github.com/google/benchmark

### Measuring the Right Thing

Interleaving

Similar to how Americans report pre-tax salary, Americans use non-PPP-adjusted stats, attention-seeking startups report revenue instead of profit, performance engineers report the best version of benchmark if not stated otherwise.

I have never seen people do that though. It makes most difference when comparing branchy and branch-free algorithms.

People report things they like to report and leave out the things they don't.

### Noise Mitigation

Frequency scaling

I use a [convenient GNOME shell extension](https://extensions.gnome.org/extension/1082/cpufreq/) that has a separate button to do it.

Since we are guiding our optimization by experiments, it is important to account for side effects and external noise in them, especially when reporting results to someone else:

- Unless you are expecting a 2x kind of improvement, treat microbenchmarking the same way as A/B testing. When you run a program on a laptop for under a second, a ±5% fluctuation in performance is normal, so if you want to revert or keep a potential +1% improvement, run it until you reach a statistical significance, by calculating variances and p-values.
- Make sure there are no cold start effects due to cache. I usually solve this by making one cold test run where I check correctness of the algorithm, and then run it many times over for benchmarking (without checking correctness).
- If you benchmark a CPU-intensive algorithm, measure its performance in cycles using `perf stat`: this way it will be independent of clock frequency, fluctuations fo which is usually the main source of noise.
- Otherwise, set core frequency to the level you expect it to be and make sure nothing interferes with it. On Linux you can do it with `cpupower` (e. g. `sudo cpupower frequency-set -g powersave` to put it to minimum or `sudo cpupower frequency-set -g ondemand` to enable turbo boost).

When running benchmarks, always quiesce the system:

- make sure no other jobs are running,
- turn turbo boost and hyper-threading off,
- turn off network and don't fiddle with the mouse,
- attach jobs to specific cores.

It is very easy to get skewed results without doing anything obviously wrong. Even a program's name can affect its speed: the executable's name ends up in an environment variable, environment variables end up on the call stack, and so the length of the name affects stack alignment, which can result in data accesses slowing down due to crossing cache line or memory page boundaries.

https://www.cs.huji.ac.il/~feit/exp/related.html

### Managing Experiments

Performance cycle is implementing, running and collecting metrics, and finding where the bottleneck is. The shorter this cycle is, the better.

If you do it correctly, working on improving performance should resemble a loop:

1. run the program and collect metrics,
2. figure out where the bottleneck is,
3. remove the bottleneck and go to step 1.

The shorter this loop is, the faster you will iterate. Here are some hints on how to set up your environment to achieve this (you can find many examples in the [code repo](https://github.com/sslotin/ahm-code) for this book):

- Separate all testing and analytics code from the implementation of the algorithm itself, and also different implementations from each other. In C/C++, you can do this by creating a single header file (e. g. `matmul.hh`) with a function interface and the code for its benchmarking in `main`, and many implementation files for each algorithm version (`v1.cc`, `v2.cc`, etc.) that all include that single header file.
- To speed up builds and reruns, create a Makefile or just a bunch of small scripts that calculate the statistics you may need.
- To speed up high-level analytics, create a Jupyter notebook where you put small scripts and do all the plots. You can also put build scripts there if you feel like it.
- To put numbers in perspective, use statistics like "ns per query" or "cycles per byte" instead of wall clock whenever it is applicable. When you start to approach very high levels of performance, it makes sense to calculate what the theoretically maximal performance is and start thinking about your algorithm performance as a fraction of it.

