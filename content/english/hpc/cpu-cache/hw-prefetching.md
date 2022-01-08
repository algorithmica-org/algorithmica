---
title: Hardware Prefetching
weight: 1
---

In the bandwidth benchmark, we iterated over array and fetched its elements. Although separately each memory read in that case is not different from the fetch in pointer chasing, they run much faster because they can are overlapped: and in fact, CPU issues read requests in advance without waiting for the old ones to complete, so that the results come about the same time as the CPU needs them.

In fact, this sometimes works even when we are not sure which instruction is going to be executed next. Consider the following example:

```cpp
bool cond = some_long_memory_operation();

if (cond)
    do_this_fast_operation();
else
    do_that_fast_operation();
```

What most modern CPUs do is they start evaluating one (most likely) branch without waiting for the condition to be computed. If they are right, then you will progress faster, and if they are wrong, the worst thing will happen is they discard some useless computation. This includes memory operations too, including cache system — because, well, we wait for a hundred cycles anyway, why not evaluate at least one of the branches ahead of time. By the way, this is what Meltdown was all about.

This general technique of hiding latency with bandwidth is called *prefetching* — and it can be either implicit or explicit. CPU automatically running ahead in the pipeline is just one way to use it. Hardware can figure out even without looking at the future instructions, and just by analyzing memory access patterns. Hiding latency is crucial — it is pretty much the single most important idea we keep coming back to in this book. Apart from having a very large pipeline and using the fact that scheduler can look ahead in it, modern memory controllers can detect simple patterns such as iterating backwards, forwards, including using constant small-ish strides.

Here is how to test it: we now generate our permutation in a way that makes us load consecutive cache lines, but we fetch elements in random order inside the cache lines.

```cpp
int p[15], q[N];

iota(p, p + 15, 1);

for (int i = 0; i + 16 < N; i += 16) {
    random_shuffle(p, p + 15);
    int k = i;
    for (int j = 0; j < 15; j++)
        k = q[k] = i + p[j];
    q[k] = i + 16;
}
```

The latency here remains constant at 3ns regardless (or whatever is the latency of pointers / bit fields implementation).

Hardware prefetching is usually powerful enough for most cases. You can iterate over multiple arrays, sometimes with small strides, or load just small amounts. It is as intelligent and detrimental to performance as branch prediction.
