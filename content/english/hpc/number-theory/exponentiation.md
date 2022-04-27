---
title: Binary Exponentiation
weight: 2
draft: true
---

You can calculate $a^{p-2}$ in $O(\log p)$ time using binary exponentiation:

```c++
int inv(int x) {
    return binpow(x, mod - 2);
}
```

To perform the Fermat test, we need to raise a number to power $n-1$, preferrably using less than $n-2$ modular multiplications. We can use the fact that multiplication is associative:

$$
\begin{aligned}
    a^{2k}       &= (a^k)^2
\\  a^{2k + 1} &= (a^k)^2 \cdot a
\end{aligned}
$$

We essentially group it like this:

$$
a^8 = (aaaa) \cdot (aaaa) = ((aa)(aa))((aa)(aa))
$$

This allows using only $O(\log n)$ operations (or, more specifically, at most $2 \cdot \log_2 n$ modular multiplications).

```c++
int binpow(int a, int n) {
    int res = 1;
    while (n) {
        if (n & 1)
            res = res * a % mod;
        a = a * a % mod;
        n >>= 1;
    }
    return res;
}
```

179.64

This helps if `n` or `mod` is a constant.

```c++
int inverse(int _a) {
    long long a = _a, r = 1;
    
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


Несколько причин:

Это выражение довольно легко вбивать (1e9+7).
Простое число.
Достаточно большое.
int не переполняется при сложении.
long long не переполняется при умножении.
Кстати, 10^9 + 910 
9
 +9 обладает всеми теми же свойствами. Иногда используют и его.

