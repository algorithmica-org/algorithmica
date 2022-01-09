---
title: Modular Inverse
weight: 1
---

In this section, we are going to discuss some preliminaries before discussing more advanced topics.

In computers, we use the 1st of January, 1970 as the start of the "Unix era", and all time computations are usually done relative to that timestamp.

We humans also keep track of time relative to some point in the past, which usually has a political or religious significance. At the moment of writing, approximately 63882260594 seconds have passed since 0 AD.

But for daily tasks, we do not really need that information. Depending on the situation, the relevant part may be that it is 2 pm right now and it's time to go to dinner, or that it's Thursday and so Subway's sub of the day is an Italian BMT. What we do is instead of using a timestamp we use its remainder, which contains just the information we need. And the beautiful thing about it is that remainders are small and cyclic. Think the hour clock: after 12 there comes 1 again, so the number is always small.

![](../img/clock.gif)

It is much easier to deal with 1- or 2-digit numbers than 11-digit ones. If we encode each day of the weak starting with Monday from 0 to 6 inclusive, Thursday is going to get number 3. But what day of the week is it going to be in one year? We need to add 365 to it and then reduce modulo 7. It is convenient that `365 % 7` is 1, so we will know that it's Friday unless it is a leap year (in which case it will be Saturday).

Modular arithmetic studies the way these sets of remainders behave, and it has fundamental applications in number theory, cryptography and data compression.


Consider the following problem: our "week" now consists of $m$ days, and we cycle through it with a steps of $a > 0$. How many distinct days there will be?

Let's assume that the first day is always Monday. At some point the sequence of day is going to cycle. The days will be representable as $k a \mod m$, so we need to find the first $k$ such as $k a$ is divisible by $m$. In the case of $m=7$, $m$ is prime, so the cycle length will be 7 exactly for any $a$.

Now, if $m$ is not prime, but it is still coprime with $a$. For $ka$ to be divisible by $m$, $k$ needs to be divisible by $m$. In general, the answer is $\frac{m}{gcd(a, m)}$. For example, if the week is 10 days long, if the starting number is even, then it will cycle through all even numbers, and if the number is 5, then it will only cycle between 0 and 5. Otherwise it will go through all 10 remainders.

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

### Primality Testing

These theorems have a lot of applications. One of them is checking whether a number $n$ is prime or not faster than factoring it. You can pick any base $a$ at random and try to raise it to power $a^{p-1}$ modulo $n$ and check if it is $1$. Such base is called *witness*.

Such probabilistic tests are therefore returning either "no" or "maybe". It may be the case that it just happened to be equal to $1$ but in fact $n$ is composite, in which case you need to repeat the test until you are okay with the false positive probability. Moreover, there exist carmichael numbers, which are composite numbers $n$ that satisfy $a^n \equiv 1 \pmod n$ for all $a$. These numbers are rare, but still [exist](https://oeis.org/A002997).

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

This helps if `n` or `mod` is a constant.

### Modular Division

"Normal" operations also apply to residues: +, -, *. But there is an issue with division, because we can't just bluntly divide two numbers: $\frac{8}{2} = 4$, но $\frac{8 \\% 5 = 3}{2 \\% 5 = 2} \neq 4$.

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
```

Another application is the exact division modulo $2^k$.

**Exercise**. Try to adapt the technique for binary GCD.
