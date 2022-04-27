---
title: Montgomery Multiplication
weight: 4
---

When we talked about [integers](../integer) in general, we discussed how to perform division and modulo by multiplication, and, unsurprisingly, in modular arithmetic 90% of its time is spent calculating modulo. Apart from using the general tricks described in the previous article, there is another method specifically for modular arithmetic, called *Montgomery multiplication*.

As all other fast reduction methods, it doesn't come for free. It works only in *Montgomery space*, so we need to transform our numbers in and out of it before doing the multiplications. This means that on top of doing some compile-time computations, we would also need to do some operations before the multiplication.

For the space we need a positive integer $r \ge n$ coprime to $n$. In practice we always choose $r$ to be $2^m$ (with $m$ usually being equal 32 or 64), since multiplications, divisions and modulo $r$ operations can then be efficiently implemented using shifts and bitwise operations. Therefore $n$ needs to be an odd number so that every power of $2$ will be coprime to $n$. And if it is not, we can make it odd (?).

The representative $\bar x$ of a number $x$ in the Montgomery space is defined as

$$
\bar{x} = x \cdot r \bmod n
$$

Note that the transformation is actually such a multiplication that we want to optimize, so it is still an expensive operation. However, we will only need to transform a number into the space once, perform as many operations as we want efficiently in that space and at the end transform the final result back, which should be profitable if we are doing lots of operations modulo $n$.

Inside the Montgomery space addition, substraction and checking for equality is performed as usual ($x \cdot r + y \cdot r \equiv (x + y) \cdot r \bmod n$). However, this is not the case for multiplication. Denoting multiplication in Montgomery space as $*$ and normal multiplication as $\cdot$, we expect the result to be:

$$
\bar{x} * \bar{y} = \overline{x \cdot y} = (x \cdot y) \cdot r \bmod n
$$

But the normal multiplication will give us:

$$
\bar{x} \cdot \bar{y} = (x \cdot y) \cdot r \cdot r \bmod n
$$

Therefore the multiplication in the Montgomery space is defined as

$$
\bar{x} * \bar{y} = \bar{x} \cdot \bar{y} \cdot r^{-1} \bmod n
$$

This means that whenever we multiply two numbers, after the multiplication we need to *reduce* them. Therefore, we need to have an efficient way of calculating $x \cdot r^{-1} \bmod n$.

### Montgomery reduction

Assume that $r=2^{64}$, the modulo $n$ is 64-bit and the number $x$ we need to reduce (multiply by $r^{-1}$) is 128-bit (the product of two 64-bit numbers).

Because $\gcd(n, r) = 1$, we know that there are two numbers $r^{-1}$ and $n'$ in the $[0, n)$ range such that

$$
r \cdot r^{-1} + n \cdot n' = 1
$$

and both $r^{-1}$ and $n'$ can be computed using the extended Euclidean algorithm.

Using this identity we can express $r \cdot r^{-1}$ as $(-n \cdot n' + 1)$ and write $x \cdot r^{-1}$ as

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

Since $x < n \cdot n < r \cdot n$ (as $x$ is a product of multiplicatio) and $q \cdot n < r \cdot n$, we know that $-n < (x - q \cdot n) / r < n$. Therefore the final modulo operation can be implemented using a single bound check and addition.

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
struct montgomery {
    u64 n, nr;
    
    montgomery(u64 n) : n(n) {
        nr = 1;
        for (int i = 0; i < 6; i++)
            nr *= 2 - n * nr;
    }

    u64 reduce(u128 x) {
        u64 q = u64(x) * nr;
        u64 m = ((u128) q * n) >> 64;
        u64 xhi = (x >> 64);
        //cout << u64(x>>64) << " " << u64(x) << " " << q << endl;
        //cout << u64(m>>64) << " " << u64(m) << endl;
        //exit(0);
        if (xhi >= m)
            return (xhi - m);
        else
            return (xhi - m) + n;
    }

    u64 mult(u64 x, u64 y) {
        return reduce((u128) x * y);
    }

    u64 transform(u64 x) {
        return (u128(x) << 64) % n;
    }
};
```

```c++
montgomery m(n);
m.transform(x);
```