---
title: Extended Euclidean Algorithm
weight: 3
---

### Primality Testing

These theorems have a lot of applications. One of them is checking whether a number $n$ is prime or not faster than factoring it. You can pick any base $a$ at random and try to raise it to power $a^{p-1}$ modulo $n$ and check if it is $1$. Such base is called *witness*.

Such probabilistic tests are therefore returning either "no" or "maybe." It may be the case that it just happened to be equal to $1$ but in fact $n$ is composite, in which case you need to repeat the test until you are okay with the false positive probability. Moreover, there exist carmichael numbers, which are composite numbers $n$ that satisfy $a^n \equiv 1 \pmod n$ for all $a$. These numbers are rare, but still [exist](https://oeis.org/A002997).

Unless the input is provided by an adversary, the mistake probability will be low. This test is adequate for finding large primes: there are roughly $\frac{n}{\ln n}$ primes among the first $n$ numbers, which is another fact that we are not going to prove. These primes are distributed more or less evenly, so one can just pick a random number and check numbers in sequence, and after checking $O(\ln n)$ numbers one will probably be found.

### Modular Division

"Normal" operations also apply to residues: +, -, *. But there is an issue with division, because we can't just bluntly divide two numbers: $\frac{8}{2} = 4$, but $\frac{8 \\% 5 = 3}{2 \\% 5 = 2} \neq 4$.

To perform division, we need to find an element that will behave itself like the reciprocal $\frac{1}{a} = a^{-1}$, and instead of "division" multiply by it. This element is called a *modular inverse*.

If the modulo is a prime number, then the solution is $a^{-1} \equiv a^{p-2}$, which follows directly from Fermat's theorem by dividing the equivalence by $a$:

$$
a^p \equiv a \implies a^{p-1} \equiv 1 \implies a^{p-2} \equiv a^{-1}
$$

This means that $a^{p-2}$ "behaves" like $a^{-1}$ which is what we need.

You can calculate $a^{p-2}$ in $O(\log p)$ time using binary exponentiation:

```c++
int inv(int x) {
    return binpow(x, mod - 2);
}
```

If the modulo is not prime, then we can still get by calculating $\phi(m)$ and invoking Euler's theorem. But calculating $\phi(m)$ is as difficult as factoring it, which is not fast. There is a more general method.

### Extended Euclidean Algorithm

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
