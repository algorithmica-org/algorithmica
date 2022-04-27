---
title: Finite Fields
weight: 5
draft: true
---

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

This exact field is a foundation of many cryptographic and data compression. In fact, when you loaded this page, your computer did a transform of everything that was communicated into this form.
