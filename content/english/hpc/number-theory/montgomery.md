---
title: Montgomery Multiplication
weight: 4
published: true
---

Unsurprisingly, a large fraction of computation in [modular arithmetic](../modular) is often spent on calculating the modulo operation, which is as slow as [general integer division](/hpc/arithmetic/division/) and typically takes 15-20 cycles, depending on the operand size.

The best way to deal this nuisance is to avoid modulo operation altogether, delaying or replacing it with [predication](/hpc/pipelining/branchless), which can be done, for example, when calculating modular sums:

```cpp
const int M = 1e9 + 7;

// input: array of n integers in the [0, M) range
// output: sum modulo M
int slow_sum(int *a, int n) {
    int s = 0;
    for (int i = 0; i < n; i++)
        s = (s + a[i]) % M;
    return s;
}

int fast_sum(int *a, int n) {
    int s = 0;
    for (int i = 0; i < n; i++) {
        s += a[i]; // s < 2 * M
        s = (s >= M ? s - M : s); // will be replaced with cmov
    }
    return s;
}

int faster_sum(int *a, int n) {
    long long s = 0; // 64-bit integer to handle overflow
    for (int i = 0; i < n; i++)
        s += a[i]; // will be vectorized
    return s % M;
}
```

However, sometimes you only have a chain of modular multiplications, and there is no good way to eel out of computing the remainder of the division — other than with the [integer division tricks](../hpc/arithmetic/division/) requiring a constant modulo and some precomputation.

But there is another technique designed specifically for modular arithmetic, called *Montgomery multiplication*.

### Montgomery Space

Montgomery multiplication works by first transforming the multipliers into *Montgomery space*, where modular multiplication can be performed cheaply, and then transforming them back when their actual values are needed. Unlike general integer division methods, Montgomery multiplication is not efficient for performing just one modular reduction and only becomes worthwhile when there is a chain of modular operations.

The space is defined by the modulo $n$ and a positive integer $r \ge n$ coprime to $n$. The algorithm involves modulo and division by $r$, so in practice, $r$ is chosen to be $2^{32}$ or $2^{64}$, so that these operations can be done with a right-shift and a bitwise AND respectively.

<!-- Therefore $n$ needs to be an odd number so that every power of $2$ will be coprime to $n$. And if it is not, we can make it odd (?). -->

**Definition.** The *representative* $\bar x$ of a number $x$ in the Montgomery space is defined as

$$
\bar{x} = x \cdot r \bmod n
$$

Computing this transformation involves a multiplication and a modulo — an expensive operation that we wanted to optimize away in the first place — which is why we only use this method when the overhead of transforming numbers to and from the Montgomery space is worth it and not for general modular multiplication.

<!-- Note that the transformation is actually such a multiplication that we want to optimize, so it is still an expensive operation. However, we will only need to transform a number into the space once, perform as many operations as we want efficiently in that space and at the end transform the final result back, which should be profitable if we are doing lots of operations modulo $n$. -->

Inside the Montgomery space, addition, substraction, and checking for equality is performed as usual:

$$
x \cdot r + y \cdot r \equiv (x + y) \cdot r \bmod n
$$

However, this is not the case for multiplication. Denoting multiplication in the Montgomery space as $*$ and the "normal" multiplication as $\cdot$, we expect the result to be:

$$
\bar{x} * \bar{y} = \overline{x \cdot y} = (x \cdot y) \cdot r \bmod n
$$

But the normal multiplication in the Montgomery space yields:

$$
\bar{x} \cdot \bar{y} = (x \cdot y) \cdot r \cdot r \bmod n
$$

Therefore, the multiplication in the Montgomery space is defined as

$$
\bar{x} * \bar{y} = \bar{x} \cdot \bar{y} \cdot r^{-1} \bmod n
$$

This means that, after we normally multiply two numbers in the Montgomery space, we need to *reduce* the result by multiplying it by $r^{-1}$ and taking the modulo — and there is an efficent way to do this particular operation.

### Montgomery reduction

Assume that $r=2^{32}$, the modulo $n$ is 32-bit, and the number $x$ we need to reduce is 64-bit (the product of two 32-bit numbers). Our goal is to calculate $y = x \cdot r^{-1} \bmod n$. 

Since $r$ is coprime with $n$, we know that there are two numbers $r^{-1}$ and $n^\prime$ in the $[0, n)$ range such that

$$
r \cdot r^{-1} + n \cdot n^\prime = 1
$$

and both $r^{-1}$ and $n^\prime$ can be computed, e.g., using the [extended Euclidean algorithm](../euclid-extended).

Using this identity, we can express $r \cdot r^{-1}$ as $(1 - n \cdot n^\prime)$ and write $x \cdot r^{-1}$ as

$$
\begin{aligned}
x \cdot r^{-1} &= x \cdot r \cdot r^{-1} / r
\\             &= x \cdot (1 - n \cdot n^{\prime}) / r
\\             &= (x - x \cdot n \cdot n^{\prime}    ) / r
\\             &\equiv (x - x \cdot n \cdot n^{\prime} + k \cdot r \cdot n) / r &\pmod n &\;\;\text{(for any integer $k$)}
\\             &\equiv (x - (x \cdot n^{\prime} - k \cdot r) \cdot n) / r &\pmod n
\end{aligned}
$$

Now, if we choose $k$ to be $\lfloor x \cdot n^\prime / r \rfloor$ (the upper 64 bits of the $x \cdot n^\prime$ product), it will cancel out, and $(k \cdot r - x \cdot n^{\prime})$ will simply be equal to $x \cdot n^{\prime} \bmod r$ (the lower 32 bits of $x \cdot n^\prime$), implying:

$$
x \cdot r^{-1} \equiv (x - x \cdot n^{\prime} \bmod r \cdot n) / r
$$

The algorithm itself just evaluates this formula, performing two multiplications to calculate $q = x \cdot n^{\prime} \bmod r$ and $m = q \cdot n$, and then subtracts it from $x$ and right-shifts the result to divide it by $r$.

The only remaining thing to handle is that the result may not be in the $[0, n)$ range; but since

$$
x < n \cdot n < r \cdot n \implies x / r < n
$$

and

$$
m = q \cdot n < r \cdot n \implies m / r < n
$$

it is guaranteed that

$$
-n < (x - m) / r < n
$$

Therefore, we can simply check if the result is negative and in that case, add $n$ to it, giving the following algorithm:

```c++
typedef __uint32_t u32;
typedef __uint64_t u64;

const u32 n = 1e9 + 7, nr = inverse(n, 1ull << 32);

u32 reduce(u64 x) {
    u32 q = u32(x) * nr;      // q = x * n' mod r
    u64 m = (u64) q * n;      // m = q * n
    u32 y = (x - m) >> 32;    // y = (x - m) / r
    return x < m ? y + n : y; // if y < 0, add n to make it be in the [0, n) range
}
```

This last check is relatively cheap, but it is still on the critical path. If we are fine with the result being in the $[0, 2 \cdot n - 2]$ range instead of $[0, n)$, we can remove it and add $n$ to the result unconditionally:

```c++
u32 reduce(u64 x) {
    u32 q = u32(x) * nr;
    u64 m = (u64) q * n;
    u32 y = (x - m) >> 32;
    return y + n
}
```

We can also move the `>> 32` operation one step earlier in the computation graph and compute $\lfloor x / r \rfloor - \lfloor m / r \rfloor$ instead of $(x - m) / r$. This is correct because the lower 32 bits of $x$ and $m$ are equal anyway since

$$
m = x \cdot n^\prime \cdot n \equiv x \pmod r
$$

But why would we voluntarily choose to perfom two right-shifts instead of just one? This is beneficial because for `((u64) q * n) >> 32` we need to do a 32-by-32 multiplication and take the upper 32 bits of the result (which the x86 `mul` instruction [already writes](../hpc/arithmetic/integer/#128-bit-integers) in a separate register, so it doesn't cost anything), and the other right-shift `x >> 32` is not on the critical path.

```c++
u32 reduce(u64 x) {
    u32 q = u32(x) * nr;
    u32 m = ((u64) q * n) >> 32;
    return (x >> 32) + n - m;
}
```

One of the main advantages of Montgomery multiplication over other modular reduction methods is that it doesn't require very large data types: it only needs a $r \times r$ multiplication that extracts the lower and higher $r$ bits of the result, which [has special support](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=7395,7392,7269,4868,7269,7269,1820,1835,6385,5051,4909,4918,5051,7269,6423,7410,150,2138,1829,1944,3009,1029,7077,519,5183,4462,4490,1944,5055,5012,5055&techs=AVX,AVX2&text=mul) on most hardware also makes it easily generalizable to [SIMD](../hpc/simd/) and larger data types:

```c++
typedef __uint128_t u128;

u64 reduce(u128 x) const {
    u64 q = u64(x) * nr;
    u64 m = ((u128) q * n) >> 64;
    return (x >> 64) + n - m;
}
```

Note that a 128-by-64 modulo is not possible with general integer division tricks: the compiler [falls back](https://godbolt.org/z/fbEE4v4qr) to calling a slow [long arithmetic library function](https://github.com/llvm-mirror/compiler-rt/blob/69445f095c22aac2388f939bedebf224a6efcdaf/lib/builtins/udivmodti4.c#L22) to support it.

### Faster Inverse and Transform

Montgomery multiplication itself is fast, but it requires some precomputation:

- inverting $n$ modulo $r$ to compute $n^\prime$,
- transforming a number *to* the Montgomery space,
- transforming a number *from* the Montgomery space.

The last operation is already efficiently performed with the `reduce` procedure we just implemented, but the first two can be slightly optimized.

**Computing the inverse** $n^\prime = n^{-1} \bmod r$ can be done faster than with the extended Euclidean algorithm by taking advantage of the fact that $r$ is a power of two and using the following identity:

$$
a \cdot x \equiv 1 \bmod 2^k
\implies
a \cdot x \cdot (2 - a \cdot x)
\equiv
1 \bmod 2^{2k}
$$

Proof:

$$
\begin{aligned}
a \cdot x \cdot (2 - a \cdot x)
   &= 2 \cdot a \cdot x - (a \cdot x)^2
\\ &= 2 \cdot (1 + m \cdot 2^k) - (1 + m \cdot 2^k)^2
\\ &= 2 + 2 \cdot m \cdot 2^k - 1 - 2 \cdot m \cdot 2^k - m^2 \cdot 2^{2k}
\\ &= 1 - m^2 \cdot 2^{2k}
\\ &\equiv 1 \bmod 2^{2k}.
\end{aligned}
$$

We can start with $x = 1$ as the inverse of $a$ modulo $2^1$ and apply this identity exactly $\log_2 r$ times, each time doubling the number of bits in the inverse — somewhat reminiscent of [the Newton's method](../hpc/arithmetic/newton/).

**Transforming** a number into the Montgomery space can be done by multiplying it by $r$ and computing modulo [the usual way](../hpc/arithmetic/division/), but we can also take advantage of this relation:

$$
\bar{x} = x \cdot r \bmod n = x * r^2
$$

Transforming a number into the space is just a multiplication by $r^2$. Therefore, we can precompute $r^2 \bmod n$ and perform a multiplication and reduction instead — which may or may not be actually faster because multiplying a number by $r=2^{k}$ can be implemented with a left-shift, while multiplication by $r^2 \bmod n$ can not.

### Complete Implementation

It is convenient to wrap everything into a single `constexpr` structure:

```c++
struct Montgomery {
    u32 n, nr;
    
    constexpr Montgomery(u32 n) : n(n), nr(1) {
        // log(2^32) = 5
        for (int i = 0; i < 5; i++)
            nr *= 2 - n * nr;
    }

    u32 reduce(u64 x) const {
        u32 q = u32(x) * nr;
        u32 m = ((u64) q * n) >> 32;
        return (x >> 32) + n - m;
        // returns a number in the [0, 2 * n - 2] range
        // (add a "x < n ? x : x - n" type of check if you need a proper modulo)
    }

    u32 multiply(u32 x, u32 y) const {
        return reduce((u64) x * y);
    }

    u32 transform(u32 x) const {
        return (u64(x) << 32) % n;
        // can also be implemented as multiply(x, r^2 mod n)
    }
};
```

To test its performance, we can plug Montgomery multiplication into the [binary exponentiation](../hpc/number-theory/exponentiation/):

```c++
constexpr Montgomery space(M);

int inverse(int _a) {
    u64 a = space.transform(_a);
    u64 r = space.transform(1);
    
    #pragma GCC unroll(30)
    for (int l = 0; l < 30; l++) {
        if ( (M - 2) >> l & 1 )
            r = space.multiply(r, a);
        a = space.multiply(a, a);
    }

    return space.reduce(r);
}
```

While vanilla binary exponentiation with a compiler-generated fast modulo trick requires ~170ns per `inverse` call, this implementation takes ~166ns, going down to ~158ns we omit `transform` and `reduce` (a reasonable use case is for `inverse` to be used as a subprocedure in a bigger modular computation). This is a small improvement, but Montgomery multiplication becomes much more advantageous for SIMD applications and larger data types.

**Exercise.** Implement efficient *modular* [matix multiplication](/hpc/algorithms/matmul).
