---
title: Extended Euclidean Algorithm
weight: 3
draft: true
---


If the modulo is not prime, then we can still get by calculating $\phi(m)$ and invoking Euler's theorem. But calculating $\phi(m)$ is as difficult as factoring it, which is not fast. There is a more general method.

Note that this is only true for prime $p$. Euler's theorem handles the case of arbitary $m$, and states that

$$
a^{\phi(m)} \equiv 1 \pmod m
$$

where $\phi(m)$ is called [Euler's totient function](https://en.wikipedia.org/wiki/Euler%27s_totient_function) and is equal to the number of residues of $m$ that is coprime with it. In particular case of when $m$ is prime, $\phi(p) = p - 1$ and we get Fermat's theorem, which is just a special case.

---

*Extended Euclidean algorithm* apart from finding $g = \gcd(a, b)$ also finds integers $x$ and $y$ such that

$$
a \cdot x + b \cdot y = g
$$

which solves the problem of finding modular inverse if we substitute $b$ with $m$ and $g$ with $1$:

$$
a^{-1} \cdot a + k \cdot m = 1
$$

Note that if $a$ is not coprime with $m$, then there will be no solution. We can still find *some* element, but it will not work for any dividend.

The algorithm is also recursive. It makes a recursive call, calculates the coefficients $x'$ and $y'$ for $\gcd(b, a \bmod b)$, and restores the general solution. If we have a solution $(x', y')$ for pair $(b, a \bmod b)$:

$$
b \cdot x' + (a \bmod b) \cdot y' = g
$$

To get the solution for the initial input, rewrite the expression $(a \bmod b)$ as $(a - \lfloor \frac{a}{b} \rfloor \cdot b)$ and subsitute it into the aforementioned equality:

$$
b \cdot x' + (a - \Big \lfloor \frac{a}{b} \Big \rfloor \cdot b) \cdot y' = g
$$

Now let's rearrange the terms (grouping by $a$ and $b$) to get

$$
a \cdot \underbrace{y'}_x + b \cdot \underbrace{(x' - \Big \lfloor \frac{a}{b} \Big \rfloor \cdot y')}_y = g
$$

Comparing it with initial expression, we infer that we can just use coefficients by $a$ and $b$ for the initial $x$ and $y$.

```c++
int gcd(int a, int b, int &x, int &y) {
    if (a == 0) {
        x = 0;
        y = 1;
        return b;
    }
    int x1, y1;
    int d = gcd(b % a, a, x1, y1);
    x = y1 - (b / a) * x1;
    y = x1;
    return d;
}

int inverse(int a) {
    int x, y;
    gcd(a, M, x, y);
    if (x < 0)
        x += M;
    return x;
}
```

159.28

```c++
int inverse(int a) {
    int b = M, x = 1, y = 0;
    while (a != 1) {
        y -= b / a * x;
        b %= a;
        swap(a, b);
        swap(x, y);
    }
    return x < 0 ? x + M : x;
}
```

134.33

Another application is the exact division modulo $2^k$.

**Exercise**. Try to adapt the technique for binary GCD.
