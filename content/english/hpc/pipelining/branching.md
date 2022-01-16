---
title: The Cost of Branching
weight: 2
---

When a CPU encounters a conditional jump or [any other type of branching](/hpc/architecture/indirect), it doesn't just sit idle until its condition is computed — instead it starts *speculatively executing* the branch that seems more likely to be taken immediately. During execution the CPU computes statistics about branches taken on each instruction, and after a while and they start to predict them by recognizing common patterns.

For this reason, the true "cost" of a branch largely depends on how well it can be predicted by the CPU. If it is a pure 50/50 coin toss, you have to suffer a [control hazard](../hazards) and discard the entire pipeline, taking another 15-20 cycles to build up again. And if the branch is always or never taken, you pay almost nothing except checking the condition.

## An Experiment

As a case study, we are going to create an array of random integers between 0 and 99 inclusive:

```c++
for (int i = 0; i < N; i++)
    a[i] = rand() % 100;
```

Then we create a loop where we sum up all its elements under 50:

```c++
volatile int s;

for (int i = 0; i < N; i++)
    if (a[i] < 50)
        s += a[i];
```

We set $N = 10^6$ and run this loop many times over so that cold cache effects doesn't mess up our results. We mark our accumulator variable as `volatile` so that the compiler doesn't vectorize the loop, interleave its iterations, or "cheat" in any other way.

On Clang, this produces assembly that looks like this:

```nasm
    mov  rcx, -4000000
    jmp  body
counter:
    add  rcx, 4
    jz   finished
body:
    mov  edx, dword ptr [rcx + a + 4000000]
    cmp  edx, 49
    jg   counter
    add  dword ptr [rsp + 12], edx
    jmp  counter
```

Our goal is to simulate a completely unpredictable branch, and we successfully achieve it: the code takes ~14 CPU cycles per element. For a very rough estimate of what it is supposed to be, we can assume that the branches alternate between "<" and ">=", and the pipeline is mispredicted every other iteration. Then, every two iterations:

- We discard the pipeline, which is 19 cycles deep on Zen 2 (i. e. it has 19 stages, each taking one cycle).
- We need a memory fetch and a comparison, which costs ~5 cycles. We can check the conditions of even and odd iterations concurrently, so let's assume we only pay it once per 2 iterations.
- In case of the "<" branch, we need another ~4 cycles to add `a[i]` to a volatile (memory-stored) variable `s`.

Therefore, on average, we need to spend $(4 + 5 + 19) / 2 = 14$ cycles per element, matching what we measured.

### Branch Prediction

We can replace the hardcoded 50% with a tweakable parameter `P`, which effectively corresponds to the probability of the "<" branch:

```c++
for (int i = 0; i < N; i++)
    if (a[i] < P)
        s += a[i];
```

Now, if we benchmark it for different values of `P`, we get an interesting-looking graph:

![](../img/probabilities.svg)

It's peak is at 50-55%, as expected: branch misprediction is the most expensive thing here. This graph is asymmetrical: it takes just ~1 cycle to only check conditions that are never satisfied (`P = 0`), and ~7 cycles for the sum if the branch is always taken (`P = 7`).

An interesting detail is that this graph is not unimodal: there is another local minimum at around 85-90%. We spend ~6.15 cycles per element there, or about 10-15% faster compared to when we always take the branch, accounting for the fact that we need to perform less additions. Branch misprediction stop affecting performance at this point, because it happens, not the whole instruction buffer is discarded, but only the operations that were speculatively scheduled. That 10-15% mispredict rate is the equilibrium point where we can see far enough in the pipeline not to stall, but save 10-15% on taking the cheaper ">=" branch.

### Pattern Detection

Here, everything that was needed of a branch prediction is a hardware statistics counter: if we went to branch A more often than to branch B, then it makes sense to speculatively execute branch A. But branch predictors on modern CPUs are considerably more advanced than that and can detect much more complicated patterns.

Let's fix `P` back at 50, and then sort the array first before the main summation loop:

```c++
for (int i = 0; i < N; i++)
    a[i] = rand() % 100;

std::sort(a, a + n);
```

We are still processing the same elements, but in different order, and instead of 14 cycles, it now runs in a little bit more than 4, which is exactly the average of the cost of the pure "<" and ">=" branches.

The branch predictor pick up on much more complicated patterns than just "always left, then always right" or "left-right-left-right". If we just decrease the size of the array $N$ to 1000 (without sorting it), then branch predictor memorizes the entire sequence of branches, and the benchmark again measures at around 4 — in fact, even slightly less than in the sorted array, because in the former case branch predictor needs to spend some time flicking between the "always yes" and "always no" states.

### Likeliness of Branches

Because of array layout issues. Using `[[likely]]` and `[[unlikely]]` attributes like this:

```c++
for (int i = 0; i < N; i++)
    if (a[i] < 90) [[likely]]
        s += a[i];
```

It doesn't communicate anything to the branch predictor. Instead, it [changes the machine code layout](/hpc/architecture/layout) so that the rare branch doesn't obstruct the pipeline.

For this reason, runtime exceptions and base case checks usually don't really cost anything if they are indeed rare.

If the branches are fundamentally unpredictable, there is another idea. You can just get rid of branches — which we are going to explore in [the next section](../branchless).

### Acknowledgements

This case study is inspired by [the most upvoted Stack Overflow question ever](https://stackoverflow.com/questions/11227809/why-is-processing-a-sorted-array-faster-than-processing-an-unsorted-array).
