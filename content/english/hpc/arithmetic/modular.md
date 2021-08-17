---
title: Finite Fields and Modular Arithmetic
weight: 5
---

In this section, we are going to discuss some preliminaries before discussing more advanced topics.

In computers, we use the 1st of January, 1970 as the start of the "Unix era", and all time computations are ususally done relative to that timestamp.

We humans also keep track of time relative to some point in the past, which usually has a political or religious significance. At the moment of writing, approximately 63882260594 seconds have passed since 0 AD.

But for daily tasks, we do not really need that information. Depending on the situation, the relevant part may be that it is 2 pm right now and it's time to go to dinner, or that it's Thursday and so Subway's sub of the day is an Italian BMT. What we do is instead of using a timestamp we use its remainder, which contains just the information we need. And the beautiful thing about it is that remainders are small and cyclic. Think the hour clock: after 12 there comes 1 again, so the number is always small.

![](../img/clock.gif)

It is much easier to deal with 1- or 2-digit numbers than 11-digit ones. If we encode each day of the weak starting with Monday from 0 to 6 inclusive, Thursday is going to get number 3. But what day of the week is it going to be in one year? We need to add 365 to it and then reduce modulo 7. It is convenient that `365 % 7` is 1, so we will know that it's Friday unless it is a leap year (in which case it will be Saturday).

Modular arithmetic studies the way these sets of remainders behave, and it has fundamental applications in number theory, cryptography and data compression.

## Modular Arithmetic

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

where $\phi(m)$ is called Euler's totent function and is equal to the number of residues of $m$ that is coprime with it. In particular case of when $m$ is prime, $\phi(p) = p - 1$ and we get Fermat's theorem, which is just a special case.

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

**Exercise**. Adapt the technique for binary GCD. Do it myself?

## Montgomery Multiplication

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
// TODO fix me and prettify me
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

## Abstract Algebra

There are other mathematical objects that behave the same way as remainders modulo a prime numbers. Based on what properties these sets of objects retain they are called *groups*, *rings* and *fields*.

### Permutations

We can definie product of permutations as application of one permutation to another.

This operation is associative, so we can use binary exponentiation to compute $n$-th power in $O(n \log n)$ time.

![](../img/permutation.png)

In general, this is called *permutation group*, and *groups* are sets of element that have an operation defined on them.

### Roots of unity

Complex numbers are numbers of form $a + bi$, where $a$ and $b$ are real numbers and $i$ is called imaginary one: it is the number for which $i^2 = -1$.

Complex numbers are useful in algebra to work with roots of negative numbers, as $i$ in some sense is equal to $\sqrt{-1}$. Similar to negative numbers, they don't really exist in the real world, but only in the minds of mathematicians.

It is most convenient to think about complex numbers geometrically.

*Modulus* of a complex number as the real number $r = \sqrt{a^2 + b^2}$. Geometrically, this is the length of vector $(a, b)$.

*Argument* of a complex number is the real number $\phi \in (-\pi, \pi]$, for which $\tan \phi = \frac{b}{a}$. Geometrically, this is the angle between vectors $(a, 0)$ и $(a, b)$.

This way we can represent a complex number using polar coordinates:

$$
a + bi = r \cdot ( \cos \phi + i \sin \phi )
$$

![](../img/complex-plane.png)

The reason this representation is useful is because if we need to multiply two complex numbers it can be shown with high school trigonometry that instead of doing binomial expansion we just need to multiply their moduli and add their arguments:

$$
\begin{aligned}
(a + bi) \cdot (c + di)
   &= r_1 \cdot ( \cos \phi_1 + i \sin \phi_1 ) \cdot r_2 \cdot ( \cos \phi_2 + i \sin \phi_2 )
\\ &= r_1 \cdot r_2 \cdot (\cos \phi_1 \cos \phi_2 - \sin \phi_1 \sin \phi_2 + i \cos \phi_1 \sin \phi_2 + i \cos \phi_2 \sin \phi_1 )
\\ &= r_1 \cdot r_2 \cdot (\cos (\phi_1 + \phi_2) + i \sin (\phi_1 + \phi_2) )
\end{aligned}
$$

Now, let's **define** Euler's number $e$ as the number for which

$$
e^{i\phi} = \cos \phi + i \sin \phi
$$

that is, let's just introduce such notation for $(\cos \phi + i \sin \phi)$ without thinking too much about what raising a number to a complex exponent really means. Geometrically, all such points will live on a unitary circle.

Such notation is useful, because we can treat $e^{i\phi}$ as a normal exponent. If we want to multiply two numbers complex on a unit circle with arguments $a$ and $b$, then we just write

$$
(\cos a + i \sin a) \cdot (\cos b + i \sin b) = e^{i (a+b)}
$$

Now, what does all that have to do with finite rings you may ask. The thing is that when we multiply complex numbers that live on a unit circle they wrap around the same way integer remainders do. There are still infinitely many of them, so the resemblence is not clear, but consider this: how many $n$-th *roots* of one there can be? These are the points that when raised to $n$-th power arrive at 1.

It turns out that there are exactly $n$ of them, and they will be equally spaced. Precisely, these will be numbers of form

$$
w_k = e^{i \tau \frac{k}{n}}
$$

where $\tau$ means $2 \pi$ (a [modern notation](https://tauday.com/tau-manifesto)).

![](../img/roots.png)

The first root $w_1$ (the second root, to be more precise, because $1$ is also a root) is called generating root of unity. Raising it to 1st, 2nd and so on powers will generate a sequence of roots that will cycle after $n$ iterations.

$$
w_n = e^{i \tau \frac{n}{n}} = e^{i \tau} = e^{i \cdot 0} = w_0 = 1
$$

Everything not on unit circle will have moduli too large or too low. And everything with argument not divided by $w_1$ will have argument too off.

Structures like these are called *rings*, or, more precisely, *finite rings*.

### Galois Fields

Remainders are *finite rings*. What makes remainders modulo a prime different is that there will always exist an inverse operation for multiplication, in which case it is called a *finite fields*. But prime numbers are not the only set sizes that can house a finite field.

The problem with having finite fields of prime numbers is that they are wasteful when dealing with computers, that have power-of-two data.

It turns out that you can also construct fields of size $p^k$, for any prime $p$. This is particulary useful for computers, because you can set $p=2$ and $k=8$, and one byte will perfectly fit for members of this set.

For non-prime fields, you move away from the idea of using integers, and instead you encode information as a special type of polynomial. First, you pick an *irriducible polynomial*. For example, for GF(8), that $p(x) = x3 + x + 1$ is the one: it can't be factored into a product.

You define a member of the set by the coefficient of the polynomial. Since every coefficient is either 0 or 1, there will be exactly 256 of them.

You define addition as xor-ing its elements, and multiplication as multiplying the polynomials and reducing them by that irreducible polynomial (which can be done in a manner similar to GCD).

Xor-ing is okay computationally, but instead of doing this weird multiplication we can just exploit the fact that there are not that many of them and just precompute a lookup table of 256 one-byte entries.

This sounds complicated, but it is all done to have efficient implementations:

```c++
char log[256], ilog[256];

char add(char x, char y) {
    return x ^ y;
}

char sub(char x, char y) {
    return x ^ y;
}

char mul(char x, char y) {
    return ilog[log[x] + log[y]];
}

char div(char x, char y) {
    return ilog[log[x] - log[y]];
}
```

This exact field is a foundation of many cryptographic and data compression. In fact, when you loaded this page, your computer did a transform of everytihnf that was communicated into this form.
