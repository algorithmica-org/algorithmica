---
title: Modular Inverse
weight: 1
---

<!--

In this section, we are going to discuss some preliminaries before discussing more advanced topics.

we use the 1st of January, 1970 as the start of the "Unix era," and all time computations are usually done relative to that timestamp.

And the beautiful thing about it is that remainders are small and cyclic. Think the hour clock: after 12 there comes 1 again, so the number is always small.

![](../img/clock.gif)

-->

Computers usually store time as the number of seconds that have passed since the 1st of January, 1970 — the start of the "Unix era" — and use these timestamps in all computations that have to do with time.

We humans also keep track of time relative to some point in the past, which usually has a political or religious significance. For example, at the moment of writing, approximately 63882260594 seconds have passed since 0 AD.

But unlike computers, we do not always need *all* that information. Depending on the task at hand, the relevant part may be that it's 2 pm right now and it's time to go to dinner, or that it's Thursday and so Subway's sub of the day is an Italian BMT. Instead of the whole timestamp, we use its *remainer* containing just the information we need: it is much easier to deal with 1- or 2-digit numbers than 11-digit ones.

### Modular Arithmetic

Two integers $a$ and $b$ are said to be *congruent* modulo $m$ if $m$ divides their difference:

$$
m \mid (a - b) \; \Longleftrightarrow \; a \equiv b \pmod m
$$

Congruence modulo $m$ is an equivalence relation, which splits all integers into equivalence classes, called *residues*. Each residue class modulo $m$ may be represented by any one of its members — although we commonly use the smallest nonnegative integer of that class (equal to the remainder $x \bmod m$ for all nonnegative $x$).

<!--

Equivalently, the *remainders* of their division by $m$ should be equal:

a \bmod m = b \bmod m

Here are a few example of how this can be useful.

-->

*Modular arithmetic* studies these sets of residues, which are fundamental for number theory.

**Problem.** Today is Thursday. What day of the week it will be exactly in a year?

If we enumerate each day of the week starting with Monday from $0$ to $6$ inclusive, Thursday gets number $3$. To find out what day it is going to be in a year from now, we need to add $365$ to it and then reduce modulo $7$. Conveniently, $365 \bmod 7 = 1$, so we know that it will be Friday unless it is a leap year (in which case it will be Saturday).

**Problem.** Our "week" now consists of $m$ days, and our year consists of $a$ days (no leap years). How many distinct days of the week there will be among one, two, three and so on whole years from now?

For simplicity, assume that today is Monday, so that the initial day number $d_0$ is zero and after each year, it changes to

$$
d_{k + 1} = (d_k + a) \bmod m
$$

After $k$ years, it will be

$$
d_k = k \cdot a \bmod m
$$

Since there are only $m$ days in a week, at some point it will be Monday again, and the sequence of day numbers is going to cycle. The number of distinct days is the length of this cycle, so we need to find the smallest $k$ such that

$$
k \cdot a \equiv 0 \pmod m
$$

First of all, if $a \equiv 0$, it will be ethernal Monday. We now assume the non-trivial case of $a \not \equiv 0$.

For a seven-day week, $m = 7$ is prime. There is no $k$ smaller than $m$ such that $k \cdot a$ is divisible by $m$ because $m$ can not be decomposed in such a product by the definition of primality. So, if $m$ is prime, we will cycle through all of $m$ week days.

If $m$ is not prime, but $a$ is *coprime* with it (that is, $a$ and $m$ do not have common divisors), then the answer is still $m$ for the same reason: the divisors of $a$ do not help in zeroing out the product any faster.

If $a$ and $m$ share some divisors, then it is only possible to get residues that are also divisible by them. For example, if the week is $m = 10$ days long, and the year has $a = 42$ or any other even number of days, then we will cycle through all even day numbers, and if the number of days is a multiple of $5$, then we will only oscillate between $0$ and $5$. Otherwise, we will go through all the $10$ remainders.

Therefore, in general, the answer is $\frac{m}{\gcd(a, m)}$, where $\gcd(a, m)$ is the [greatest common divisor](/hpc/algorithms/gcd/) of $a$ and $m$.

### Fermat's Theorem

Now, consider what happens if instead of adding a number $a$, we repeatedly multiply by it, that is, write numbers in the form $a^n \mod m$. Since these are all finite numbers there is going to be a cycle, but what will its length be? If $p$ is prime, it turns out, all of them.

**Theorem.** $a^p \equiv a \pmod p$ for all $a$ that are not multiple of $p$.

**Proof**. Let $P(x_1, x_2, \ldots, x_n) = \frac{k}{\prod (x_i!)}$ be the *multinomial coefficient*, that is, the number of times the element $a_1^{x_1} a_2^{x_2} \ldots a_n^{x_n}$ would appear after the expansion of $(a_1 + a_2 + \ldots + a_n)^k$. Then

$$
\begin{aligned}
a^p &= (\underbrace{1+1+\ldots+1+1}_\text{$a$ times})^p &
\\\ &= \sum_{x_1+x_2+\ldots+x_a = p} P(x_1, x_2, \ldots, x_a) & \text{(by defenition)}
\\\ &= \sum_{x_1+x_2+\ldots+x_a = p} \frac{p!}{x_1! x_2! \ldots x_a!} & \text{(which terms will not be divisible by $p$?)}
\\\ &\equiv P(p, 0, \ldots, 0) + \ldots + P(0, 0, \ldots, p) & \text{(everything else will be canceled)}
\\\ &= a
\end{aligned}
$$

and then dividing by $a$ gives us the Fermat's theorem.

Note that this is only true for prime $p$. Euler's theorem handles the case of arbitary $m$, and states that

$$
a^{\phi(m)} \equiv 1 \pmod m
$$

where $\phi(m)$ is called Euler's totient function and is equal to the number of residues of $m$ that is coprime with it. In particular case of when $m$ is prime, $\phi(p) = p - 1$ and we get Fermat's theorem, which is just a special case.

Несколько причин:

Это выражение довольно легко вбивать (1e9+7).
Простое число.
Достаточно большое.
int не переполняется при сложении.
long long не переполняется при умножении.
Кстати, 10^9 + 910 
9
 +9 обладает всеми теми же свойствами. Иногда используют и его.

### Primality Testing

These theorems have a lot of applications. One of them is checking whether a number $n$ is prime or not faster than factoring it. You can pick any base $a$ at random and try to raise it to power $a^{p-1}$ modulo $n$ and check if it is $1$. Such base is called *witness*.

Such probabilistic tests are therefore returning either "no" or "maybe." It may be the case that it just happened to be equal to $1$ but in fact $n$ is composite, in which case you need to repeat the test until you are okay with the false positive probability. Moreover, there exist carmichael numbers, which are composite numbers $n$ that satisfy $a^n \equiv 1 \pmod n$ for all $a$. These numbers are rare, but still [exist](https://oeis.org/A002997).

Unless the input is provided by an adversary, the mistake probability will be low. This test is adequate for finding large primes: there are roughly $\frac{n}{\ln n}$ primes among the first $n$ numbers, which is another fact that we are not going to prove. These primes are distributed more or less evenly, so one can just pick a random number and check numbers in sequence, and after checking $O(\ln n)$ numbers one will probably be found.

### Binary Exponentiation

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
