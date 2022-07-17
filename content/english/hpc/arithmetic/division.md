---
title: Integer Division
weight: 6
---

Compared to other arithmetic operations, division works very poorly on x86 and computers in general. Both floating-point and integer division is notoriously hard to implement in hardware. The circuitry takes a lot of space in the ALU, the computation has a lot of stages, and as the result, `div` and its siblings routinely take 10-20 cycles to complete, with latency being slightly less on smaller data type sizes.

### Division and Modulo in x86

Since nobody wants to duplicate all this mess for a separate modulo operation, the `div` instruction serves both purposes. To perform a 32-bit integer division, you need to put the dividend *specifically* in the `eax` register and call `div` with the divisor as its sole operand. After this, the quotient will be stored in `eax` and the remainder will be stored in `edx`.

The only caveat is that the dividend actually needs to be stored in *two* registers, `eax` and `edx`: this mechanism enables 64-by-32 or even 128-by-64 division, similar to how [128-bit multiplication](../integer) works. When performing the usual 32-by-32 signed division, we need to sign-extend `eax` to 64 bits and store its higher part in `edx`:

```nasm
div(int, int):
    mov  eax, edi
    cdq
    idiv esi
    ret
```

For unsigned division, you can just set `edx` to zero so that it doesn't interfere:

```nasm
div(unsigned, unsigned):
    mov  eax, edi
    xor  edx, edx
    div  esi
    ret
```

An in both cases, in addition to the quotient in `eax`, you can also access the remainder as `edx`:

```nasm
mod(unsigned, unsigned):
    mov  eax, edi
    xor  edx, edx 
    div  esi
    mov  eax, edx
    ret
```

You can also divide 128-bit integer (stored in `rdx:rax`) by a 64-bit integer:

```nasm
div(u128, u64):
    ; a = rdi + rsi, b = rdx
    mov  rcx, rdx
    mov  rax, rdi
    mov  rdx, rsi
    div  edx 
    ret
```

The high part of the dividend should be less than the divisor, otherwise an overflow occurs. Because of this constraint, it is [hard](https://danlark.org/2020/06/14/128-bit-division/) to get compilers to produce this code by themselves: if you divide a [128-bit integer type](../integer) by a 64-bit integer, the compiler will bubble-wrap it with additional checks which may actually be unnecessary.

### Division by Constants

Integer division is painfully slow, even when fully implemented in hardware, but it can be avoided in certain cases if the divisor is constant. A well-known example is the division by a power of two, which can be replaced by a one-cycle binary shift: the [binary GCD algorithm](/hpc/algorithms/gcd) is a delightful showcase of this technique.

In the general case, there are several clever tricks that replace division with multiplication at the cost of a bit of precomputation. All these tricks are based on the following idea. Consider the task of dividing one floating-point number $x$ by another floating-point number $y$, when $y$ is known in advance. What we can do is to calculate a constant

$$
d \approx y^{-1}
$$

and then, during runtime, we will calculate

$$
x / y = x \cdot y^{-1} \approx x \cdot d
$$

The result of $\frac{1}{y}$ will be at most $\epsilon$ off, and the multiplication $x \cdot d$ will only add another $\epsilon$ and therefore will be at most $2 \epsilon + \epsilon^2 = O(\epsilon)$ off, which is tolerable for the floating-point case.

<!--
For example, `double` has 53 mantissa bits and therefore a machine epsilon of $\frac{1}{53}$, , if we also make sure it is rounded the right way.
-->

### Barrett Reduction

How to generalize this trick for integers? Calculating `int d = 1 / y` doesn't seem to work, because it will just be zero. The best thing we can do is to express it as

$$
d = \frac{m}{2^s}
$$

and then find a "magic" number $m$ and a binary shift $s$ such that `x / y == (x * m) >> s` for all `x` within range.

$$
  \lfloor x / y \rfloor
= \lfloor x \cdot y^{-1} \rfloor
= \lfloor x \cdot d \rfloor
= \lfloor x \cdot \frac{m}{2^s} \rfloor
$$

It can be shown that such a pair always exists, and compilers actually perform an optimization like that by themselves. Every time they encounter a division by a constant, they replace it with a multiplication and a binary shift. Here is the generated assembly for dividing an `unsigned long long` by $(10^9 + 7)$:

```nasm
;  input (rdi): x
; output (rax): x mod (m=1e9+7)
mov    rax, rdi
movabs rdx, -8543223828751151131  ; load magic constant into a register
mul    rdx                        ; perform multiplication
mov    rax, rdx
shr    rax, 29                    ; binary shift of the result
```

This technique is called *Barrett reduction*, and it's called "reduction" because it is mostly used for modulo operations, which can be replaced with a single division, multiplication and subtraction by the virtue of this formula:

$$
r = x - \lfloor x / y \rfloor \cdot y
$$

This method requires some precomputation, including performing one actual division. Therefore, this is only beneficial when you perform not just one but a few divisions, all with the same constant divisor.

### Why It Works

It is not very clear why such $m$ and $s$ always exist, let alone how to find them. But given a fixed $s$, intuition tells us that $m$ should be as close to $2^s/y$ as possible for $2^s$ to cancel out. So there are two natural choices: $\lfloor 2^s/y \rfloor$ and $\lceil 2^s/y \rceil$. The first one doesn't work, because if you substitute

$$
\Bigl \lfloor \frac{x \cdot \lfloor 2^s/y \rfloor}{2^s} \Bigr \rfloor
$$

then for any integer $\frac{x}{y}$ where $y$ is not even, the result will be strictly less than the truth. This only leaves the other case, $m = \lceil 2^s/y \rceil$. Now, let's try to derive the lower and upper bounds for the result of the computation:

$$
  \lfloor x / y \rfloor
= \Bigl \lfloor \frac{x \cdot m}{2^s} \Bigr \rfloor
= \Bigl \lfloor \frac{x \cdot \lceil  2^s /y \rceil}{2^s} \Bigr \rfloor
$$

Let's start with the bounds for $m$:

$$
2^s / y
\le
\lceil 2^s / y \rceil
<
2^s / y + 1
$$

And now for the whole expression:

$$
x / y - 1
<
\Bigl \lfloor \frac{x \cdot \lceil  2^s /y \rceil}{2^s} \Bigr \rfloor
<
x / y + x / 2^s
$$

We can see that the result falls somewhere in a range of size $(1 + \frac{x}{2^s})$, and if this range always has exactly one integer for all possible $x / y$, then the algorithm is guaranteed to give the right answer. Turns out, we can always set $s$ to be high enough to achieve it.

What will be the worst case here? How to pick $x$ and $y$ so that the $(x/y - 1, x/y + x / 2^s)$ range contains two integers? We can see that integer ratios don't work because the left border is not included, and assuming $x/2^s < 1$, only $x/y$ itself will be in the range. The worst case is actually the $x/y$ that comes closest to $1$ without exceeding it. For $n$-bit integers, that is the second-largest possible integer divided by the first-largest:

$$
\begin{aligned}
    x = 2^n - 2
\\  y = 2^n - 1
\end{aligned}
$$

In this case, the lower bound will be $(\frac{2^n-2}{2^n-1} - 1)$ and the upper bound will be $(\frac{2^n-2}{2^n-1} + \frac{2^n-2}{2^s})$. The left border is as close to a whole number as possible, and the size of the whole range is the second largest possible. And here is the punchline: if $s \ge n$, then the only integer contained in this range is $1$, and so the algorithm will always return it.

### Lemire Reduction

Barrett reduction is a bit complicated, and also generates a length instruction sequence for modulo because it is computed indirectly. There is a new ([2019](https://arxiv.org/pdf/1902.01961.pdf)) method, which is simpler and actually faster for modulo in some cases. It doesn't have a conventional name yet, but I am going to refer to it as [Lemire](https://lemire.me/blog/) reduction.

Here is the main idea. Consider the floating-point representation of some integer fraction:

$$
\frac{179}{6} = 11101.1101010101\ldots = 29\tfrac{5}{6} \approx 29.83
$$

How can we "dissect" it to get the parts we need?

- To get the integer part (29), we can just floor or truncate it before the dot.
- To get the fractional part (⅚), we can just take what is after the dots.
- To get the remainder (5), we can multiply the fractional part by the divisor.

Now, for 32-bit integers, we can set $s = 64$ and look at the computation that we do in the multiply-and-shift scheme:

$$
  \lfloor x / y \rfloor
= \Bigl \lfloor \frac{x \cdot m}{2^s} \Bigr \rfloor
= \Bigl \lfloor \frac{x \cdot \lceil  2^s /y \rceil}{2^s} \Bigr \rfloor
$$

What we really do here is we multiply $x$ by a floating-point constant ($x \cdot m$) and then truncate the result $(\lfloor \frac{\cdot}{2^s} \rfloor)$.

What if we took not the highest bits but the lowest? This would correspond to the fractional part — and if we multiply it back by $y$ and truncate the result, this will be exactly the remainder:

$$
r = \Bigl \lfloor \frac{ (x \cdot \lceil  2^s /y \rceil \bmod 2^s) \cdot y }{2^s} \Bigr \rfloor
$$

This works perfectly because what we do here can be interpreted as just three chained floating-point multiplications with the total relative error of $O(\epsilon)$. Since $\epsilon = O(\frac{1}{2^s})$ and $s = 2n$, the error will always be less than one, and hence the result will be exact.

```c++
uint32_t y;

uint64_t m = uint64_t(-1) / y + 1; // ceil(2^64 / y)

uint32_t mod(uint32_t x) {
    uint64_t lowbits = m * x;
    return ((__uint128_t) lowbits * y) >> 64; 
}

uint32_t div(uint32_t x) {
    return ((__uint128_t) m * x) >> 64;
}
```

We can also check divisibility of $x$ by $y$ with just one multiplication using the fact that the remainder of division is zero if and only if the fractional part (the lower 64 bits of $m \cdot x$) does not exceed $m$ (otherwise, it would become a nonzero number when multiplied back by $y$ and right-shifted by 64).

```c++
bool is_divisible(uint32_t x) {
    return m * x < m;
}
```

The only downside of this method is that it needs integer types four times the original size to perform the multiplication, while other reduction methods can work with just the double.

There is also a way to compute 64x64 modulo by carefully manipulating the halves of intermediate results; the implementation is left as an exercise to the reader.

### Further Reading

Check out [libdivide](https://github.com/ridiculousfish/libdivide) and [GMP](https://gmplib.org/) for more general implementations of optimized integer division.

It is also worth reading [Hacker's Delight](https://www.amazon.com/Hackers-Delight-2nd-Henry-Warren/dp/0321842685), which has a whole chapter dedicated to integer division.
