---
title: Vector Extensions
weight: 2
---

If you feel like the design of C++ intrinsics is terrible, you are not alone. I've spent dozens of hours on the intel intrinsics guide, and I still can't remember whether I need to type `_mm256` or `__m256`.

They are not only hard to use, but also neither portable nor maintainable. A good software is the one where we don't need to implement multiple procedure for each CPU, and just write it once, in architecture-agnostic way.

One day, compiler engineers from the GNU Project thought the same way and developed a special vector types that feel more like arrays with some operators overloaded to match to relevant instructions.

In GCC, here is how you can define vector of 8 integers packed into 256-bit (32-byte) register:

```c++
typedef int v8si __attribute__ (( vector_size(32) ));
// type ^   ^ typename          size in bytes ^ 
```

Unfortunately, this syntax is not universal, so different compilers may use different syntax.

There is somewhat of a naming convention, which is to include size and type of elements into the name of the type. In this case, we defined a "vector of 8 signed integers". But you may choose any name you want, like `vec`, `reg` or whatever. The only thing you don't want to do is to name it `vector` because of how much headache and confusion there will be because of `std::vector`.

The main advantage of using these types is that for many operations you can use normal C++ operators instead of looking up the relevant intrinsic.

```c++
v4si a = {1, 2, 3, 5};
v4si b = {8, 13, 21, 34};

v4si c = a + b;

for (int i = 0; i < 4; i++)
    printf("%d\n", c[i]);

c *= 2; // multiply by scalar

for (int i = 0; i < 4; i++)
    printf("%d\n", c[i]);
```

Let's rewrite the same "a + b" loop using vector types:

```c++
typedef double v4d __attribute__ (( vector_size(32) ));
v4d a[100/4], b[100/4], c[100/4];

for (int i = 0; i < 100/4; i++)
    c[i] = a[i] + b[i];
```

Armed with a nicer syntax, let's consider a slightly more complex example: summing up an array. The naive approach is not so straightforward to vectorize, because the state of the loop (sum of the current prefix) depends on the previous iteration:

```c++
int sum_naive(int *a, int n) {
    int s = 0;
    for (int i = 0; i < n; i++)
        s += a[i];
    return s;
}
```

The way to overcome this is to split a single scalar accumulator (`s`) into 8 separate ones, where $s_i$ would contain the sum of $\\{ a_{8 \cdot j + i } \\}$, that is, every 8th element of the original array, shifted by $i$. If we store the 8 accumulators in a 256-bit vector, we can update them all at once by adding consecutive 8-elements segments of the array:

```c++
int sum_simd(v8si *a, int n) {
    //       ^ you can just cast a pointer normally, like with any other pointer type
    v8si s = {0};

    for (int i = 0; i < n / 8; i++)
        s += a[i];
    
    int res = 0;
    
    // sum 8 accumulators into one 
    for (int i = 0; i < 8; i++)
        res += s[i];

    // add the remainder of a
    for (int i = n / 8 * 8; i < n; i++)
        res += a[i];
        
    return res;
}
```

The part where we sum up 8 accumulators to get the total sum can be done a bit faster by what's called a "horizontal sum", which is the repeated use of [special instructions](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#techs=AVX,AVX2&text=_mm256_hadd_epi32&expand=2941) that add together pairs of adjacent elements:

```c++
int hsum(v8si s) {
    // TODO
    // https://stackoverflow.com/questions/42000693/why-my-avx2-horizontal-addition-function-is-not-faster-than-non-simd-addition
}
```

Although this is approximately how compilers vectorize array reductions, this is not the fastest way to do it. We will [come back](../../instruction-level-parallelism/throughput) to this problem in the next chapter.

Vector extensions are much clearer compared to the intrinsic nightmare, but some things that we may want to do are just not expressible with native C++ constructs, so we will still need intrinsics—which is not a exclusive choice, because vector types support conversion to "`_mm`" types and back. We will try, however, to avoid doing so as much as possible.
