---
title: Argmin with SIMD
weight: 7
---

Computing the *minimum* of an array is [easily vectorizable](/hpc/simd/reduction), as it is not different from any other reduction: in AVX2, you just need to use a convenient `_mm256_min_epi32` intrinsic as the inner operation. It computes the minimum of two 8-element vectors in one cycle — even faster than in the scalar case, which requires at least a comparison and a conditional move.

Finding the *index* of that minimum element (*argmin*) is much harder, but it is still possible to vectorize very efficiently. In this section, we design an algorithm that computes the argmin (almost) at the speed of computing the minimum and ~15x faster than the naive scalar approach.

### Scalar Baseline

For our benchmark, we create an array of random 32-bit integers, and then repeatedly try to find the index of the minimum among them (the first one if it isn't unique):

```c++
const int N = (1 << 16);
alignas(32) int a[N];

for (int i = 0; i < N; i++)
    a[i] = rand();
```

For the sake of exposition, we assume that $N$ is a power of two, and run all our experiments for $N=2^{13}$ so that the [memory bandwidth](/hpc/cpu-cache/bandwidth) is not a concern.

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

It works at around 1.5 GFLOPS — meaning $1.5 \cdot 10^9$ values per second  processed on average, or about 0.75 values per cycle (the CPU is clocked at 2GHz).

Let's compare it to `std::min_element`:

```c++
int argmin(int *a, int n) {
    int k = std::min_element(a, a + n) - a;
    return k;
}
```

<!--

https://github.com/llvm-mirror/libcxx/blob/78d6a7767ed57b50122a161b91f59f19c9bd0d19/include/algorithm#L2489

https://github.com/gcc-mirror/gcc/blob/16e2427f50c208dfe07d07f18009969502c25dc8/libstdc%2B%2B-v3/include/bits/stl_algo.h#L5606

```nasm
lea	r8, 24[rdx]	# __first,
mov	r11d, DWORD PTR [rax]
cmp	DWORD PTR 12[rdx], r11d
cmovl	rax, r10	# __result,, __result, __first
```

```nasm
cmp	eax, r12d	# prephitmp_103, _108	
jle	.L36	#,	
mov	eax, r12d	# prephitmp_103, _108	
mov	ecx, ebp	# k, ivtmp.29	
.L36:	
lea	rdx, 4[r8]	# ivtmp.29,	
```

```nasm
cmp	eax, r12d	# prephitmp_103, _108	
jle	.L36	#,	
mov	eax, r12d	# prephitmp_103, _108	
mov	ecx, ebp	# k, ivtmp.29	
.L36:	
lea	rdx, 4[r8]	# ivtmp.29,	
```

-->

The version from GCC gives ~0.28 GFLOPS — apparently, the compiler couldn't pierce through all the abstractions. Another reminder to never use STL.

### Vector of Indices

The problem with vectorizing the scalar implementation is that there is a dependency between consequent iterations. When we optimized [array sum](/hpc/simd/reduction), we faced the same problem, and we solved it by splitting the array into 8 slices, each representing a subset of its indices with the same remainder modulo 8. We can apply the same trick here, except that we also have to take array indices into account.

When we have the consecutive elements and their indices in vectors, we can process them in parallel using [predication](/hpc/pipelining/branchless):

```c++
typedef __m256i reg;

int argmin(int *a, int n) {
    // indices on the current iteration
    reg cur = _mm256_setr_epi32(0, 1, 2, 3, 4, 5, 6, 7);
    // the current minimum for each slice
    reg min = _mm256_set1_epi32(INT_MAX);
    // its index (argmin) for each slice
    reg idx = _mm256_setzero_si256();

    for (int i = 0; i < n; i += 8) {
        // load a new SIMD block
        reg x = _mm256_load_si256((reg*) &a[i]);
        // find the slices where the minimum is updated
        reg mask = _mm256_cmpgt_epi32(min, x);
        // update the indices
        idx = _mm256_blendv_epi8(idx, cur, mask);
        // update the minimum (can also similarly use a "blend" here, but min is faster)
        min = _mm256_min_epi32(x, min);
        // update the current indices
        const reg eight = _mm256_set1_epi32(8);
        cur = _mm256_add_epi32(cur, eight);       // 
        // can also use a "blend" here, but min is faster
    }

    // find the argmin in the "min" register and return its real index

    int min_arr[8], idx_arr[8];
    
    _mm256_storeu_si256((reg*) min_arr, min);
    _mm256_storeu_si256((reg*) idx_arr, idx);

    int k = 0, m = min_arr[0];

    for (int i = 1; i < 8; i++)
        if (min_arr[i] < m)
            m = min_arr[k = i];

    return idx_arr[k];
}
```

It works at around 8-8.5 GFLOPS. There is still some inter-dependency between the iterations, so we can optimize it by considering more than 8 elements per iteration and taking advantage of the [instruction-level parallelism](/hpc/simd/reduction#instruction-level-parallelism).

This would help performance a lot, but not enough to match the speed of computing the minimum (~24 GFLOPS) because there is another bottleneck. On each iteration, we need a load-fused comparison, a load-fused minimum, a blend, and an addition — that is 4 instructions in total to process 8 elements. Since the decode width of this CPU (Zen 2) is just 4, the performance will still be limited by 8 × 2 = 16 GFLOPS even if we somehow got rid of all the other bottlenecks.

Instead, we will switch to another approach that requires fewer instructions per element.

### Branches Aren't Scary

When we run the scalar version, how often do we update the minimum?

Intuition tells us that, if all the values are drawn independently at random, then the event when the next element is less than all the previous ones shouldn't be frequent. More precisely, it equals the reciprocal of the number of processed elements. Therefore, the expected number of times the `a[i] < a[k]` condition is satisfied equals the sum of the harmonic series:

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

The compiler [optimized the machine code layout](/hpc/architecture/layout), and the CPU is now able to execute the loop at around 2 GFLOPS — a slight but sizeable improvement from 1.5 GFLOPS of the non-hinted loop.

Here is the idea: if we are only updating the minimum a dozen or so times during the entire computation, we can ditch all the vector-blending and index updating and just maintain the minimum and regularly check if it has changed. Inside this check, we can use however slow method of updating the argmin we want because it will only be called a few times.

To implement it with SIMD, all we need to do on each iteration is a vector load, a comparison, and a test-if-zero:

```c++
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
- Optimize the local argmin: instead of calculating its exact location, we can just save the index of the block and then come back at the end and find it just once. This lets us only compute the minimum on each positive check and broadcast it to a vector, which is simpler and much faster.

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

This is almost as high as it can get as just computing the minimum itself works at around 24-25 GFLOPS.

The only problem of all these branch-happy SIMD implementations is that they rely on the minimum being updated very infrequently. This is true for random input distributions, but not in the worst case. If we fill the array with a sequence of decreasing numbers, the performance of the last implementation drops to about 2.7 GFLOPS — almost 10 times as slow (although still faster than the scalar code because we only calculate the minimum on each block).

One way to fix this is to do the same thing that the quicksort-like randomized algorithms do: just shuffle the input yourself and iterate over the array in random order. This lets you avoid this worst-case penalty, but it is tricky to implement due to RNG- and [memory](/hpc/cpu-cache/prefetching)-related issues. There is a simpler solution.

### Find the Minimum, Then Find the Index

We know how to [calculate the minimum of an array](/hpc/simd/reduction) fast and how to [find an element in an array](/hpc/simd/masking#searching) fast — so why don't we just separately compute the minimum and then find it?

```c++
int argmin(int *a, int n) {
    int needle = min(a, n);
    int idx = find(a, n, needle);
    return idx;
}
```

If we implement the two subroutines optimally (check the linked articles), the performance will be ~18 GFLOPS for random arrays and ~12 GFLOPS for decreasing arrays — which makes sense as we are expected to read the array 1.5 and 2 times respectively. This isn't that bad by itself — at least we avoid the 10x worst-case performance penalty — but the problem is that this penalized performance also translates to larger arrays, when we are bottlenecked by the [memory bandwidth](/hpc/cpu-cache/bandwidth) rather than compute.

Luckily, we already know how to fix it. We can split the array into blocks of fixed size $B$ and compute the minima on these blocks while also maintaining the global minimum. When the minimum on a new block is lower than the global minimum, we update it and also remember the block number of where the global minimum currently is. After we've processed the entire array, we just return to that block and scan through its $B$ elements to find the argmin.

This way we only process $(N + B)$ elements and don't have to sacrifice neither ½ nor ⅓ of the performance:

```c++
const int B = 256;

// returns the minimum and its first block
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
    auto [needle, base] = approx_argmin(a, n);
    int idx = find(a + base, B, needle);
    return base + idx;
}
```

This results for the final implementation are ~22 and ~19 GFLOPS for random and decreasing arrays respectively.

The full implementation, including both `min()` and `find()`, is about 100 lines long. [Take a look](https://github.com/sslotin/amh-code/blob/main/argmin/combined.cc) if you want, although it is still far from being production-grade.

### Summary

Here are the results combined for all implementations:

```
algorithm    rand   decr   reason for the performance difference
-----------  -----  -----  -------------------------------------------------------------
std          0.28   0.28   
scalar       1.54   1.89   efficient branch prediction
+ hinted     1.95   0.75   wrong hint
index        8.17   8.12
simd         8.51   1.65   scalar-based argmin on each iteration
+ ilp        10.22  1.74   ^ same
+ optimized  22.44  2.70   ^ same, but faster because there are less inter-dependencies
min+find     18.21  12.92  find() has to scan the entire array
+ blocked    22.23  19.29  we still have an optional horizontal minimum every B elements
```

Take these results with a grain of salt: the measurements are [quite noisy](/hpc/profiling/noise), they were done for just for two input distributions, for a specific array size ($N=2^{13}$, the size of the L1 cache), for a specific architecture (Zen 2), and for a specific and slightly outdated compiler (GCC 9.3) — the compiler optimizations were also very fragile to little changes in the benchmarking code.

There are also still some minor things to optimize, but the potential improvement is less than 10% so I didn't bother. One day I may pluck up the courage, optimize the algorithm to the theoretical limit, handle the non-divisible-by-block-size array sizes and non-aligned memory cases, and then re-run the benchmarks properly on many architectures, with p-values and such. In case someone does it before me, please [ping me back](http://sereja.me/).

### Acknowledgements

The first, index-based SIMD algorithm was [originally designed](http://0x80.pl/notesen/2018-10-03-simd-index-of-min.html) by Wojciech Muła in 2018.

Thanks to Zach Wegner for [pointing out](https://twitter.com/zwegner/status/1491520929138151425) that the performance of the Muła's algorithm is improved when implemented manually using intrinsics (I originally used the [GCC vector types](/hpc/simd/intrinsics/#gcc-vector-extensions)).

<!--

Thanks to Alexander Monakov for [being meticulous](https://twitter.com/_monoid/status/1491827976438231049) and pushing me to investigate the STL version.

-->

After publication, I've discovered that [Marshall Lochbaum](https://www.aplwiki.com/wiki/Marshall_Lochbaum), the creator of [BQN](https://mlochbaum.github.io/BQN/), designed a [very similar algorithm](https://forums.dyalog.com/viewtopic.php?f=13&t=1579&sid=e2cbd69817a17a6e7b1f76c677b1f69e#p6239) while he was working on Dyalog APL in 2019. Pay more attention to the world of array programming languages!
