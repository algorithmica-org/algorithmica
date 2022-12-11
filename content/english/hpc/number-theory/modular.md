---
title: Modular Arithmetic
weight: 1
---

<!--

TODO: use it in binary exponentiation.

In this section, we are going to discuss some preliminaries before discussing more advanced topics.

we use the 1st of January, 1970 as the start of the "Unix era," and all time computations are usually done relative to that timestamp.

And the beautiful thing about it is that remainders are small and cyclic. Think the hour clock: after 12 there comes 1 again, so the number is always small.

![](../img/clock.gif)

-->

Computers usually store time as the number of seconds that have passed since the 1st of January, 1970 — the start of the "Unix era" — and use these timestamps in all computations that have to do with time.

We humans also keep track of time relative to some point in the past, which usually has a political or religious significance. For example, at the moment of writing, approximately 63882260594 seconds have passed since 1 AD — [6th century Eastern Roman monks' best estimate](https://en.wikipedia.org/wiki/Anno_Domini) of the day Jesus Christ was born.

But unlike computers, we do not always need *all* that information. Depending on the task at hand, the relevant part may be that it's 2 pm right now, and it's time to go to dinner; or that it's Thursday, and so Subway's sub of the day is an Italian BMT. Instead of the whole timestamp, we use its *remainder* containing just the information we need: it is much easier to deal with 1- or 2-digit numbers than 11-digit ones.

**Problem.** Today is Thursday. What day of the week will be exactly in a year?

If we enumerate each day of the week, starting with Monday, from $0$ to $6$ inclusive, Thursday gets number $3$. To find out what day it is going to be in a year from now, we need to add $365$ to it and then reduce modulo $7$. Conveniently, $365 \bmod 7 = 1$, so we know that it will be Friday unless it is a leap year (in which case it will be Saturday).

### Residues

**Definition.** Two integers $a$ and $b$ are said to be *congruent* modulo $m$ if $m$ divides their difference:

$$
m \mid (a - b) \; \Longleftrightarrow \; a \equiv b \pmod m
$$

For example, the 42nd day of the year is the same weekday as the 161st since $(161 - 42) = 119 = 17 \times 7$.

Congruence modulo $m$ is an equivalence relation that splits all integers into equivalence classes called *residues*. Each residue class modulo $m$ may be represented by any one of its members — although we commonly use the smallest nonnegative integer of that class (equal to the remainder $x \bmod m$ for all nonnegative $x$).

<!--

Equivalently, the *remainders* of their division by $m$ should be equal:

a \bmod m = b \bmod m

Here are a few example of how this can be useful.

-->

*Modular arithmetic* studies these sets of residues, which are fundamental for number theory.

**Problem.** Our "week" now consists of $m$ days, and our year consists of $a$ days (no leap years). How many distinct days of the week there will be among one, two, three and so on whole years from now?

For simplicity, assume that today is Monday, so that the initial day number $d_0$ is zero, and after each year, it changes to

$$
d_{k + 1} = (d_k + a) \bmod m
$$

After $k$ years, it will be

$$
d_k = k \cdot a \bmod m
$$

Since there are only $m$ days in a week, at some point, it will be Monday again, and the sequence of day numbers is going to cycle. The number of distinct days is the length of this cycle, so we need to find the smallest $k$ such that

$$
k \cdot a \equiv 0 \pmod m
$$

First of all, if $a \equiv 0$, it will be eternal Monday. Now, assuming the non-trivial case of $a \not \equiv 0$:

- For a seven-day week, $m = 7$ is prime. There is no $k$ smaller than $m$ such that $k \cdot a$ is divisible by $m$ because $m$ can not be decomposed in such a product by the definition of primality. So, if $m$ is prime, we will cycle through all of $m$ weekdays.
- If $m$ is not prime, but $a$ is *coprime* with it (that is, $a$ and $m$ do not have common divisors), then the answer is still $m$ for the same reason: the divisors of $a$ do not help in zeroing out the product any faster.
- If $a$ and $m$ share some divisors, then it is only possible to get residues that are also divisible by them. For example, if the week is $m = 10$ days long, and the year has $a = 42$ or any other even number of days, then we will cycle through all even day numbers, and if the number of days is a multiple of $5$, then we will only oscillate between $0$ and $5$. Otherwise, we will go through all the $10$ remainders.

Therefore, in general, the answer is $\frac{m}{\gcd(a, m)}$, where $\gcd(a, m)$ is the [greatest common divisor](/hpc/algorithms/gcd/) of $a$ and $m$.

### Fermat's Theorem

Now, consider what happens if, instead of adding a number $a$, we repeatedly multiply by it, writing out a sequence of

$$
d_n = a^n \bmod m
$$

Again, since there is a finite number of residues, there is going to be a cycle. But what will its length be? Turns out, if $m$ is prime, it will span all $(m - 1)$ non-zero residues.

**Theorem.** For any $a$ and a prime $p$:

$$
a^p \equiv a \pmod p
$$

**Proof**. Let $P(x_1, x_2, \ldots, x_n) = \frac{k}{\prod (x_i!)}$ be the *multinomial coefficient:* the number of times the element $a_1^{x_1} a_2^{x_2} \ldots a_n^{x_n}$ appears after the expansion of $(a_1 + a_2 + \ldots + a_n)^k$. Then:

$$
\begin{aligned}
a^p &= (\underbrace{1+1+\ldots+1+1}_\text{$a$ times})^p &
\\\ &= \sum_{x_1+x_2+\ldots+x_a = p} P(x_1, x_2, \ldots, x_a) & \text{(by definition)}
\\\ &= \sum_{x_1+x_2+\ldots+x_a = p} \frac{p!}{x_1! x_2! \ldots x_a!} & \text{(which terms will not be divisible by $p$?)}
\\\ &\equiv P(p, 0, \ldots, 0) + \ldots + P(0, 0, \ldots, p) & \text{(everything else will be canceled)}
\\\ &= a
\end{aligned}
$$

Note that this is only true for prime $p$. We can use this fact to test whether a given number is prime faster than by factoring it: we can pick a number $a$ at random, calculate $a^{p} \bmod p$, and check whether it is equal to $a$ or not.

This is called *Fermat primality test*, and it is probabilistic — only returning either "no" or "maybe" — since it may be that $a^p$ just happened to be equal to $a$ despite $p$ being composite, in which case you need to repeat the test with a different random $a$ until you are satisfied with the false positive probability.

Primality tests are commonly used to generate large primes (for cryptographic purposes). There are roughly $\frac{n}{\ln n}$ primes among the first $n$ numbers (a fact that we are not going to prove), and they are distributed more or less evenly. One can just pick a random number from the required range, perform a primality check, and repeat until a prime is found, performing $O(\ln n)$ trials on average.

An extremely bad input to the Fermat test is the [Carmichael numbers](https://en.wikipedia.org/wiki/Carmichael_number), which are composite numbers $n$ that satisfy $a^{n-1} \equiv 1 \pmod n$ for all relatively prime $a$. But these are [rare](https://oeis.org/A002997), and the chance of randomly bumping into it is low.

### Modular Division

Implementing most "normal" arithmetic operations with residues is straightforward. You only need to take care of integer overflows and remember to take modulo:

```c++
c = (a + b) % m;
c = (a - b + m) % m;
c = a * b % m;
```

But there is an issue with division: we can't just bluntly divide two residues. For example, $\frac{8}{2} = 4$, but

$$
\frac{8 \bmod 5}{2 \bmod 5} = \frac{3}{2} \neq 4
$$

To perform modular division, we need to find an element that "acts" like the reciprocal $\frac{1}{a} = a^{-1}$ and multiply by it. This element is called a *modular multiplicative inverse*, and Fermat's theorem can help us find it when the modulo $p$ is a prime. When we divide its equivalence twice by $a$, we get:

$$
a^p \equiv a \implies a^{p-1} \equiv 1 \implies a^{p-2} \equiv a^{-1}
$$

Therefore, $a^{p-2}$ is like $a^{-1}$ for the purposes of multiplication, which is what we need from a modular inverse of $a$.
