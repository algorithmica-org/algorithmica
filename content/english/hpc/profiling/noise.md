---
title: Noise Mitigation
weight: 5
---

Frequency scaling

### Removing Noise

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