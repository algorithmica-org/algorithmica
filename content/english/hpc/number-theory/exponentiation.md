---
title: Binary Exponentiation
weight: 2
draft: true
---

In modular arithmetic and computational algebra in general, you often need to raise a number to the $n$-th power — to do [modular division](../modular/#modular-division), perform [primality tests](../modular/#fermats-theorem), or compute some combinatorial values — ­and you usually want to spend fewer than $\Theta(n)$ operations calculating it.

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

### Implementation

Since we already have a recurrence, it is natural to implement the algorithm as a case matching recursive function:

```c++
const int M = 1e9 + 7; // modulo
typedef unsigned long long u64;

u64 binpow(u64 a, u64 n) {
    if (n == 0)
        return 1;
    if (n % 2 == 1)
        return binpow(a, n - 1) * a % M;
    else {
        u64 b = binpow(a, n / 2) % M;
        return b * b % m;
    }
}
```

Since $m$ is a compile-time constant, the compiler can optimize the modulo by [replacing it with multiplication](/hpc/arithmetic/division/) (even if it is not a compile-time constant, it is still cheaper to compute the magic constants by hand once).

The execution path and hence the running time depends on the value of $n$. In our benchmark, we use $m = 10^9+7$ and $n = m - 2$ so that we compute the [multiplicative inverse](../modular/#modular-division) of $a$ modulo $m$. This modulo is commonly used in competitive programming to calculate checksums in combinatorial problems because it is prime (allowing inverse via binary exponentiation), sufficiently large, doesn't overflow `int` for addition, doesn't overflow `long long` for multiplication, and is easy to type as `1e9 + 7`.

```c++
u64 inverse(u64 a) {
    return binpow(a, M - 2);
}
```

For this particular $n$, the recursive implementation takes around 400ns per call.

As recursion introduces some [overhead](/hpc/architecture/functions/)

Эта реализация рекурсивная, что работает долго. Попробуем «развернуть» рекурсию и получить итеративную.

Рассмотрим двоичное представление числа $n$. Результат $a^n$ можно представить как произведение $a$ в степенях каких-то степеней двоек. Например, если $n = 42 = 32 + 8 + 2$, то

$$
a^{42} = a^{32+8+2} = a^{32} \cdot a^8 \cdot a^2 
$$

Чтобы посчитать это произведение итеративно, пройдемся по всем битам числа $n$, поддерживая две переменные: непосредственно результат и текущее значение $a^{2^k}$, где $k$ это номер текущей итерации. На каждом шаге будем домножать $a^{2^k}$ на текущий результат, если $k$-тый бит числа $n$ единичный, и в любом случае возводить её в квадрат, получая $a^{2^k \cdot 2} = a^{2^{k+1}}$ для следующей итерации.

Стоит отметить, что во многих языках программирования бинарное возведение в степень уже реализовано. Но не в C++: функция `pow` из стандартной библиотеки реализована только для действительных чисел и использует приближенные методы, и поэтому не дает точных результатов для целочисленных аргументов.



We essentially group it like this:

$$
a^8 = (aaaa) \cdot (aaaa) = ((aa)(aa))((aa)(aa))
$$

This allows using only $O(\log n)$ operations (or, more specifically, at most $2 \cdot \log_2 n$ modular multiplications).



You can calculate $a^{p-2}$ in $O(\log p)$ time using binary exponentiation:


To perform the Fermat test, we need to raise a number to power $n-1$, preferrably using less than $n-2$ modular multiplications.

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

179.64

This helps if `n` or `mod` is a constant.

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

171.68
