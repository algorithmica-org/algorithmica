---
title: Binary Exponentiation
weight: 2
---

In modular arithmetic (and computational algebra in general), you often need to raise a number to the $n$-th power — to do [modular division](../modular/#modular-division), perform [primality tests](../modular/#fermats-theorem), or compute some combinatorial values — ­and you usually want to spend fewer than $\Theta(n)$ operations calculating it.

*Binary exponentiation*, also known as *exponentiation by squaring*, is a method that allows for computation of the $n$-th power using $O(\log n)$ multiplications, relying on the following observation:

$$
\begin{aligned}
    a^{2k}       &= (a^k)^2
\\  a^{2k + 1}   &= (a^k)^2 \cdot a
\end{aligned}
$$

To compute $a^n$, we can recursively compute $a^{\lfloor n / 2 \rfloor}$, square it, and then optionally multiply by $a$ if $n$ is odd, corresponding to the following recurrence:

$$
a^n = f(a, n) = \begin{cases}
   1,               && n = 0
\\ f(a, \frac{n}{2})^2,     && 2 \mid n
\\ f(a, n - 1) \cdot a, && 2 \nmid n
\end{cases}
$$

Since $n$ is at least halved every two recursive transitions, the depth of this recurrence and the total number of multiplications will be at most $O(\log n)$.

### Recursive Implementation

As we already have a recurrence, it is natural to implement the algorithm as a case matching recursive function:

```c++
const int M = 1e9 + 7; // modulo
typedef unsigned long long u64;

u64 binpow(u64 a, u64 n) {
    if (n == 0)
        return 1;
    if (n % 2 == 1)
        return binpow(a, n - 1) * a % M;
    else {
        u64 b = binpow(a, n / 2);
        return b * b % M;
    }
}
```

In our benchmark, we use $n = m - 2$ so that we compute the [multiplicative inverse](../modular/#modular-division) of $a$ modulo $m$:

```c++
u64 inverse(u64 a) {
    return binpow(a, M - 2);
}
```

We use $m = 10^9+7$, which is a modulo value commonly used in competitive programming to calculate checksums in combinatorial problems — because it is prime (allowing inverse via binary exponentiation), sufficiently large, not overflowing `int` in addition, not overflowing `long long` in multiplication, and easy to type as `1e9 + 7`.

Since we use it as compile-time constant in the code, the compiler can optimize the modulo by [replacing it with multiplication](/hpc/arithmetic/division/) (even if it is not a compile-time constant, it is still cheaper to compute the magic constants by hand once and use them for fast reduction).

The execution path — and consequently the running time — depends on the value of $n$. For this particular $n$, the baseline implementation takes around 330ns per call. As recursion introduces some [overhead](/hpc/architecture/functions/), it makes sense to unroll the implementation into an iterative procedure.

### Iterative Implementation

The result of $a^n$ can be represented as the product of $a$ to some powers of two — those that correspond to 1s in the binary representation of $n$. For example, if $n = 42 = 32 + 8 + 2$, then

$$
a^{42} = a^{32+8+2} = a^{32} \cdot a^8 \cdot a^2 
$$

To calculate this product, we can iterate over the bits of $n$ maintaining two variables: the value of $a^{2^k}$ and the current product after considering $k$ lowest bits of $n$. On each step, we multiply the current product by $a^{2^k}$ if the $k$-th bit of $n$ is set, and, in either case, square $a^k$ to get $a^{2^k \cdot 2} = a^{2^{k+1}}$ that will be used on the next iteration.

```c++
u64 binpow(u64 a, u64 n) {
    u64 r = 1;
    
    while (n) {
        if (n & 1)
            r = res * a % M;
        a = a * a % M;
        n >>= 1;
    }
    
    return r;
}
```

The iterative implementation takes about 180ns per call. The heavy calculations are the same; the improvement mainly comes from the reduced dependency chain: `a = a * a % M` needs to finish before the loop can proceed, and it can now execute concurrently with `r = res * a % M`.

The performance also benefits from $n$ being a constant, [making all branches predictable](/hpc/pipelining/branching/) and letting the scheduler know what needs to be executed in advance. The compiler, however, does not take advantage of it and does not unroll the `while(n) n >>= 1` loop. We can rewrite it as a `for` loop that performs constant 30 iterations:

```c++
u64 inverse(u64 a) {
    u64 r = 1;
    
    #pragma GCC unroll(30)
    for (int l = 0; l < 30; l++) {
        if ( (M - 2) >> l & 1 )
            r = r * a % M;
        a = a * a % M;
    }

    return r;
}
```

This forces the compiler to generate only the instructions we need, shaving off another 10ns and making the total running time ~170ns.

Note that the performance depends not only on the binary length of $n$, but also on the number of binary 1s. If $n$ is $2^{30}$, it takes around 20ns less as we don't have to to perform any off-path multiplications.
