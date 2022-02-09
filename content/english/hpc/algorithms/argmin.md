---
title: Argmin with SIMD
weight: 7
---

Computing the *minimum* of an array [easily vectorizable](/hpc/simd/reduction), as it is not different from any other reduction: in AVX2, you just need to use a convenient `_mm256_min_epi32` intrinsic as the inner operation. It computes the minimum of two 8-element vectors in one cycle — even faster than in the scalar case, which requires at least a comparison and a conditional move.

Finding the index of that minimum element (*argmin*) is much harder, but it is still possible to compute very fast.

### Baseline

For our benchmark, we create an array of random 32-bit integers, and then repeatedly try to find the index of the minimum among them (the first one if it isn't unique):

```c++
const int N = (1 << 16);
alignas(32) int a[N];

for (int i = 0; i < N; i++)
    a[i] = rand();
```

For the sake of exposition, we assume that $N$ is a power of two.

To implement argmin in the scalar case, we just need to maintain the index instead of the minimum value:

```c++
int argmin(int *a, int n) {
    int k = 0;

    for (int i = 0; i < n; i++)
        if (a[i] < a[k])
            k = i;
    
    return k;
}
```

It works in around 1.5 GFLOPS — meaning 1.5 values per cycle processed on average.

Let's compare it to `std::min_element`:

```c++
int argmin(int *a, int n) {
    int k = std::min_element(a, a + n) - a;
    return k;
}
```

When using the version from GCC, it gives 0.28 GFLOPS — apparently, the compiler couldn't pierce through all the abstractions. Another reminder to never use STL.

### Vector of Indices

The problem with vectorizing the scalar implementation is that there is a dependency between iterations. When we optimized [array sum](/hpc/simd/reduction), we faced the same problem, and we solved it by splitting the array into 8 slices, each representing a subset of its indices with the same remainder modulo 8.

We can apply the same trick here, except that we also have to take array indices into account. When we have both the consecutive data and indices in vectors, we can process them in parallel using [predication](/hpc/pipelining/branchless) like this:

```c++
typedef int vec __attribute__ (( vector_size(32) ));

int argmin(int *a, int n) {
    vec *v = (vec*) a;
    
    vec cur = {0, 1, 2, 3, 4, 5, 6, 7}; // indices on the current iteration
    vec min = INT_MAX + vec{};          // the current minimum for each slice
    vec idx;                            // its index (argmin) for each slice

    for (int i = 0; i < n / 8; i++) {
        vec mask = (v[i] < min);   // find the slices where the minimum updated
        min = (mask ? v[i] : min); // update the minimum
        idx = (mask ? cur : idx);  // update the indices
        cur += 8;                  // increment the current indices
    }
    
    // find the argmin in the "min" array: 

    int k = 0, m = min[0];

    for (int i = 1; i < 8; i++)
        if (min[i] < m)
            m = min[k = i];

    return idx[k]; // return its real index
}
```

It works in around 4 GFLOPS. There is still some inter-dependency between the iterations, so we can optimize it by considering more than 8 elements per iteration and taking advantage of the [instruction-level parallelism](/hpc/simd/reduction#instruction-level-parallelism). But it won't improve the performance by a lot: on each iteration, we need a load, vector comparison, two blends, and a vector addition — that is 5 instructions in total to process 8 elements. Since the decode width of this CPU (Zen 2) is just 4, the performance will still be limited by ⅘ × 8 = 6.4 GFLOPS even if we get rid of the other bottlenecks.

Instead, we will switch to another approach that requires fewer instructions per element.

### Branches Aren't Scary

When we run the scalar version, how often do we update the minimum?

Intuition tells that, if all the values are drawn independently at random, then the event when the next element is less than all the previous ones shouldn't be frequent. More formally, the expected number of times the `a[i] < a[k]` condition is satisfied equals the sum of the harmonic series:

$$
\frac{1}{2} + \frac{1}{3} + \frac{1}{4} + \ldots + \frac{1}{n} = O(\ln(n))
$$

So the minimum is updated around 5 times for a hundred-element array, 7 for a thousand-element, and just 14 for a million-element array — which isn't large at all when looked at as a fraction of all is-new-minimum checks.

The compiler probably couldn't figure it out on its own, so let's [explicitly provide](/hpc/compilation/situational) this information:

```c++
int argmin(int *a, int n) {
    int k = 0;

    for (int i = 0; i < n; i++)
        if (a[i] < a[k]) [[unlikely]]
            k = i;
    
    return k;
}
```

The compiler [optimized the machine layout](/hpc/architecture/layout), and the CPU is now able to execute the loop at around 2 GFLOPS — a slight but sizeable improvement from 1.5 GFLOPS of the non-hinted loop.

Here is the idea: if we are only updating the minimum a dozen or so times during the entire computation, we can ditch all the vector-blending and index updating and just maintain the minimum and regularly check if it has changed. Inside this check, we can use however slow method of updating the argmin we want because it will only be called a few times. 

To implement it with SIMD, all we need to do on each iteration is a vector load, a comparison, and a test-if-zero:

```c++
typedef __m256i reg;

int argmin(int *a, int n) {
    int min = INT_MAX, idx = 0;
    
    reg p = _mm256_set1_epi32(min);

    for (int i = 0; i < n; i += 8) {
        reg y = _mm256_load_si256((reg*) &a[i]); 
        reg mask = _mm256_cmpgt_epi32(p, y);
        if (!_mm256_testz_si256(mask, mask)) { [[unlikely]]
            for (int j = i; j < i + 8; j++)
                if (a[j] < min)
                    min = a[idx = j];
            p = _mm256_set1_epi32(min);
        }
    }
    
    return idx;
}
```

It already performs at ~8.5 GFLOPS, but now the loop is bottlenecked by the `testz` instruction which only has a throughput of one. The solution is to load two consecutive SIMD blocks and use the minimum of them so that the `testz` effectively processes 16 elements in one go:

```c++
int argmin(int *a, int n) {
    int min = INT_MAX, idx = 0;
    
    reg p = _mm256_set1_epi32(min);

    for (int i = 0; i < n; i += 16) {
        reg y1 = _mm256_load_si256((reg*) &a[i]);
        reg y2 = _mm256_load_si256((reg*) &a[i + 8]);
        reg y = _mm256_min_epi32(y1, y2);
        reg mask = _mm256_cmpgt_epi32(p, y);
        if (!_mm256_testz_si256(mask, mask)) { [[unlikely]]
            for (int j = i; j < i + 16; j++)
                if (a[j] < min)
                    min = a[idx = j];
            p = _mm256_set1_epi32(min);
        }
    }
    
    return idx;
}
```

This version works in ~10 GFLOPS. To remove the other obstacles, we can do two things:

- Increase the block size to 32 elements to allow for more instruction-level parallelism.
- Optimize the local argmin: instead of calculating its exact location, we can just save the index of the block, and then come back at the end and find it just once. This lets us only compute the minimum on each positive check and broadcast it to a vector, which is simpler and much faster.

With these two optimizations implemented, the performance increases to a whopping ~22 GFLOPS:

```c++
int argmin(int *a, int n) {
    int min = INT_MAX, idx = 0;
    
    reg p = _mm256_set1_epi32(min);

    for (int i = 0; i < n; i += 32) {
        reg y1 = _mm256_load_si256((reg*) &a[i]);
        reg y2 = _mm256_load_si256((reg*) &a[i + 8]);
        reg y3 = _mm256_load_si256((reg*) &a[i + 16]);
        reg y4 = _mm256_load_si256((reg*) &a[i + 24]);
        y1 = _mm256_min_epi32(y1, y2);
        y3 = _mm256_min_epi32(y3, y4);
        y1 = _mm256_min_epi32(y1, y3);
        reg mask = _mm256_cmpgt_epi32(p, y1);
        if (!_mm256_testz_si256(mask, mask)) { [[unlikely]]
            idx = i;
            for (int j = i; j < i + 32; j++)
                min = (a[j] < min ? a[j] : min);
            p = _mm256_set1_epi32(min);
        }
    }

    for (int i = idx; i < idx + 31; i++)
        if (a[i] == min)
            return i;
    
    return idx + 31;
}
```

This is almost as high as it can get — only computing the minimum itself works at around 24-25 GFLOPS.

The only problem of all these branch-happy SIMD implementations is that they rely on the minimum being updated very infrequently. This is true for random input distributions, but not in the worst case. If we fill the array with the decreasing numbers, the performance of the last implementation drops to about 2.7 GFLOPS — almost 10 times as slow (although still faster than the scalar code because we only calculate the minimum on each block).

One way to fix this is to do the same thing that the quicksort-like randomized algorithms do: just randomize the input yourself and iterate over the array in random order. This lets you avoid this worst-case penalty, but it is tricky to implement due to RNG- and [memory](/hpc/cpu-cache/prefetching)-related issues. There is a simpler solution.

### Find the Minimum, Then Find the Index

We know how to [calculate the minimum of an array](/hpc/simd/reduction) fast and how to [find an element in an array](/hpc/simd/masking#searching) fast — so why don't we just separately compute the minimum and then find it?

```c++
int argmin(int *a, int n) {
    int needle = min(a, n);
    int idx = find(a, n, needle);
    return idx;
}
```

If we implement the two subroutines optimally (check the linked articles), the performance will be ~18 GFLOPS for random arrays and ~12 GFLOPS for decreasing arrays — which makes sense as we are expected to read the array 1.5 and 2 times respectively. This isn't that bad by itself — at least we avoid the 10x worst-case performance penalty — but the problem is that this penalized performance also translates to larger arrays when we are bottlenecked by the [memory bandwidth](/hpc/cpu-cache/bandwidth) rather than the CPU.

Luckily, we already know how to fix it. We can split the array into blocks of fixed size $B$ and compute the minimums on these blocks while also maintaining the global minimum. When the minimum on a new block is lower than the global minimum, we update it and also remember the block number of there the global minimum currently is. After we've processed the whole array, we just return to that block and process $B$ elements to find the argmin.

This way we only process $(N + B)$ elements and don't have to sacrifice neither ½ nor ⅓ of the performance:

```c++
const int B = 256;

pair<int, int> approx_argmin(int *a, int n) {
    int res = INT_MAX, idx = 0;
    for (int i = 0; i < n; i += B) {
        int val = min(a + i, B);
        if (val < res) {
            res = val;
            idx = i;
        }
    }
    return {res, idx};
}

int argmin(int *a, int n) {
    auto [needle, base] = approx_argmin(a, n); // returns the first block of
    int idx = find(a + base, B, needle);
    return base + idx;
}
```

This final implementation in~22 and ~19 GFLOPS for random and decreasing arrays respectively.

The full implementation, including both `min()` and `find()`, is about 100 lines long. If you want, you [take a look at it](https://github.com/sslotin/amh-code/blob/main/argmin/combined.cc), although it's far from production-grade.

### Summary

Here are the results combined for all implementations:

```
algorithm    rand   decr   reason for the performance difference
-----------  -----  -----  -------------------------------------------------------------
std          0.28   0.28   
scalar       1.54   1.89   efficient branch prediction
+ hinted     1.95   0.75   wrong hint
index        4.08   4.17
simd         8.51   1.65   scalar-based argmin on each iteration
+ ilp        10.22  1.74   ^ same
+ optimized  22.44  2.70   ^ same, but faster because there are less inter-dependencies
min+find     18.21  12.92  find() has to scan the entire array
+ blocked    22.23  19.29  we still have an optional horizontal minimum every B elements
```

Take these results with a grain of salt: the measurements are [quite noisy](/hpc/profiling/noise), they were done for just for two input distributions, for a specific array size ($N=2^{13}$, the size of the L1 cache), for a specific architecture (Zen 2), and for a specific and slightly outdated compiler (GCC 9.2) — the compiler optimizations were also very fragile to little changes in the benchmarking code.

There are also still some minor things to optimize, but the potential improvement is less than 10% so I didn't bother. One day I may pluck up courage, optimize the algorithm to the theoretical limit, handle the non-divisible-by-block-size array sizes and non-aligned memory cases, and then re-run the benchmarks properly on many architectures and with p-values and such. If someone does it before me, please [ping me back](http://sereja.me/).

### Acknowledgements

The first, index-based SIMD algorithm was [originally designed](http://0x80.pl/notesen/2018-10-03-simd-index-of-min.html) by Wojciech Muła in 2018.

<!--

https://stackoverflow.com/questions/9795529/how-to-find-the-horizontal-maximum-in-a-256-bit-avx-vector Norbert P. and Peter Cordes 

-->
