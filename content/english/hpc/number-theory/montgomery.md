---
title: Montgomery Multiplication
weight: 4
draft: true
---

Unsurprisingly, large fractions of computations in [modular arithmetic](../modular) are often spent on calculating the modulo operation, which is as slow as general integer division and typically taking 15-20 cycles, depending on the operand size.

The best way to deal this nuisance is to avoid modulo operation altogether, delaying or replacing it with [predication](/hpc/pipelining/branchless), which can be done when calculating sums, for example:

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

The space is defined by the modulo $n$ and a positive integer $r \ge n$ coprime to $n$. The algorithm involves division and modulo by $r$, so in practice, $r$ is chosen to be $2^m$ with $m$ being equal 32 or 64, so that these operations can be done with a right-shift and a bitwise AND respectively.

<!-- Therefore $n$ needs to be an odd number so that every power of $2$ will be coprime to $n$. And if it is not, we can make it odd (?). -->

**Definition.** The *representative* $\bar x$ of a number $x$ in the Montgomery space is defined as

$$
\bar{x} = x \cdot r \bmod n
$$

Computing this transformation involves a multiplication and a modulo — an expensive operation that we wanted to optimize away in the first place — which is why we don't use this method for general modular multiplication and only long sequences of operations where transforming numbers to and from the Montgomery space is worth it.

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

Assume that $r=2^{32}$, the modulo $n$ is 32-bit, and the number $x$ we need to reduce (multiply by $r^{-1}$ and take it modulo $n$) is the 64-bit the product of two 32-bit numbers.

By definition, $\gcd(n, r) = 1$, so we know that there are two numbers $r^{-1}$ and $n'$ in the $[0, n)$ range such that

$$
r \cdot r^{-1} + n \cdot n' = 1
$$

and both $r^{-1}$ and $n'$ can be computed using the [extended Euclidean algorithm](../euclid-extended).

Using this identity, we can express $r \cdot r^{-1}$ as $(-n \cdot n' + 1)$ and write $x \cdot r^{-1}$ as

$$
\begin{aligned}
x \cdot r^{-1} &= x \cdot r \cdot r^{-1} / r
\\             &= x \cdot (-n \cdot n^{\prime} + 1) / r
\\             &= (-x \cdot n \cdot n^{\prime} + x) / r
\\             &\equiv (-x \cdot n \cdot n^{\prime} + l \cdot r \cdot n + x) / r \bmod n
\\             &\equiv ((-x \cdot n^{\prime} + l \cdot r) \cdot n + x) / r \bmod n
\end{aligned}
$$

The equivalences hold for any integer $l$. This means that we can add or subtract an arbitrary multiple of $r$ to $x \cdot n'$, or in other words, we can compute $q = x \cdot n'$ modulo $r$.

This gives us the following algorithm to compute $x \cdot r^{-1} \bmod n$:

```python
def reduce(x):
    q = (x % r) * nr % r
    a = (x - q * n) / r
    if a < 0:
        a += n
    return a
```

Since $x < n \cdot n < r \cdot n$ and $q \cdot n < r \cdot n$, we know that

$$
-n < (x - q \cdot n) / r < n
$$

Therefore, the final modulo operation can be implemented using a single bound check and addition.

Here is an equivalent C implementation for 64-bit integers:

```c++
typedef unsigned long long u64;
typedef __uint128_t u128;

u64 reduce(u128 x) {
    u64 q = u64(x) * nr;
    u64 m = ((u128) q * n) >> 64;
    u64 xhi = (x >> 64);
    if (xhi >= m)
        return (xhi - m);
    else
        return (xhi - m) + n;
}
```

We also need to implement calculating calculating the inverse of $n$ (`nr`) and transformation of numbers in and our of Montgomery space. Before providing complete implementation, let's discuss how to do that smarter, although they are just done once.

To transfer a number back from the Montgomery space we can just use Montgomery reduction.

### Fast inverse

For computing the inverse $n' = n^{-1} \bmod r$ more efficiently, we can use the following trick inspired from the Newton's method:

$$
a \cdot x \equiv 1 \bmod 2^k
\implies
a \cdot x \cdot (2 - a \cdot x)
\equiv
1 \bmod 2^{2k}
$$

This can be proven this way:

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

This means we can start with $x = 1$ as the inverse of $a$ modulo $2^1$, apply the trick a few times and in each iteration we double the number of correct bits of $x$.

### Fast transformation

Although we can just multiply a number by $r$ and compute one modulo the usual way, there is a faster way that makes use of the following relation:

$$
\bar{x} = x \cdot r \bmod n = x * r^2
$$

Transforming a number into the space is just a multiplication inside the space of the number with $r^2$. Therefore we can precompute $r^2 \bmod n$ and just perform a multiplication and reduction instead.

### Complete Implementation

```c++
typedef __uint32_t u32;
typedef __uint64_t u64;

struct montgomery {
    u32 n, nr;
    
    constexpr montgomery(u32 n) : n(n), nr(1) {
        for (int i = 0; i < 6; i++)
            nr *= 2 - n * nr;
    }

    u32 reduce(u64 x) const {
        u32 q = u32(x) * nr;
        u32 m = ((u64) q * n) >> 32;
        u32 xhi = (x >> 32);
        return xhi + n - m;
        
        // if you need 
        // u32 t = xhi - m;
        // return xhi >= m ? t : t + n;
    }

    u32 multiply(u32 x, u32 y) const {
        return reduce((u64) x * y);
    }

    u32 transform(u32 x) const {
        return (u64(x) << 32) % n;
    }
};
```

```c++
montgomery m(n);

a = m.transform(a);
b = m.transform(b);
c = m.multiply(a, b);
c = m.reduce(c);
```

```c++
int inverse(int _a) {
    u32 a = space.transform(_a);
    u32 r = space.transform(1);
    
    int n = M - 2;
    while (n) {
        if (n & 1)
            r = space.multiply(r, a);
        a = space.multiply(a, a);
        n >>= 1;
    }
    
    return space.reduce(r);
}
```

SIMD

166.79 ns

207.04 ns

```c++
constexpr montgomery space(M);

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

**Exercise.** Implement efficient *modular* [matix multiplication](/hpc/algorithms/matmul).
