---
title: Integer Arithmetic
weight: 3
---

If you are reading this chapter sequentially from the beginning, you might be wondering: why would I introduce integer arithmetic after floating-point one? Isn't it supposed to be simpler?

This is true: plain integer representations are simpler. But, counterintuitively, their simplicity allows for more possibilities for operations to be expressed in terms of others. And if floating-point representations are so unwieldy that most of their operations are implemented in hardware, efficiently manipulating integers requires much more creative use of the instruction set.

## Binary Formats

*Unsigned integers* are just natural numbers written in binary:

$$
\begin{aligned}
   5_{10}   &= 101_2 = 4 + 1
\\ 42_{10}  &= 101010_2 = 32 + 8 + 2
\\ 256_{10} &= 100000000_2 = 2^8
\end{aligned}
$$

When the result of an operation can't fit into the word size (e. g. is more or equal to $2^{32}$ for 32-bit unsigned integers), it *overflows* by leaving only the lowest 32 bits of the result. Similarly, if the result is a negative value, it *underflows* by adding it to $2^{32}$, so that it always stays in the $[0, 2^{32})$ range.

This is equivalent to performing all operations modulo a power of two:

$$
\begin{aligned}
    256                 &\equiv 0 \pmod {2^8}
\\  2021                &\equiv 229 \pmod {2^8}
\\  -42 \equiv 256 - 42 &\equiv 214 \pmod {2^8}
\end{aligned}
$$

In either case, it raises a special flag which you can check, but typically when people explicitly use unsigned integers they are expecting this behavior.

### Signed Integers

*Signed integers* support storing negative values by dedicating the highest bit to represent the sign of the number, in a similar fashion as floating-point number do. This halves the range of representable non-negative numbers: the maximum possible 32-bit integer is now $(2^{31}-1)$ and not $(2^{32}-1)$. But the encoding of negative values is not quite the same as for floating-point numbers.

Computer engineers are even lazier than programmers — and this is not only motivated by the instinctive desire of simplification, but also by saving transistor space. This can achieved by reusing circuitry that you already have for other operations, which is what they aimed for when designing the signed integer format:

- For a $n$-bit signed integer type, the encodings of all numbers in the $[0, 2^{n-1})$ range remains the same as their unsigned binary representation.
- All numbers in the $[-2^{n-1}, 0)$ range are encoded sequentially right after the "positive" range — that is, starting with $(-2^{n - 1})$ that has code $(2^{n-1})$ and ending with $(-1)$ that has code $(2^n - 1)$.

Essentially, all negative numbers are just encoded as if they were subtracted from $2^n$ — an operation known as *two's complement*:

$$
\begin{aligned}
-x &= 2^{32} - x
\\ &= \bar{x} + 1
\end{aligned}
$$

Here $\bar{x}$ represents bitwise negation, which can be also though of as subtracting $x$ from $(2^n - 1)$.

As an exercise, here are some facts about signed integers:

- All positive numbers and zero remain the same as their binary notation.
- All negative numbers have the highest bit set to zero.
- There are more negative numbers than positive numbers (exactly by one — because of zero).
- For `int`, if you add $1$ to $(2^{31}-1)$, the result will be $-2^{31}$, represented as `10000000` (for exposition purposes, we will only write 8 bits instead of 32).
- Knowing a binary notation of a positive number `x`, you can get the binary notation of `-x` as `~x + 1`.
- `-1` is represented as `~1 + 1 = 11111110 + 00000001 = 11111111`.
- `-42` is represented as `~42 + 1 = 11010101 + 00000001 = 11010110`.
- The number `-1 = 11111111` is followed by `0 = -1 + 1 = 11111111 + 00000001 = 00000000`.

The main advantage of this encoding is that you don't have to do anything to convert unsigned integers to signed ones (except maybe check for overflow), and you can reuse the same circuitry for most operations, possibly only flipping the sign bit for comparisons and such.

That said, you need to be carefull with signed integer overflows. Even though they almost always overflow the same way as unsigned integers, programming languages usually consider the possibility of overflow as undefined behavior. If you need to overflow integer variables, convert them to unsigned integers: it's free anyway.

### Integer Types

Integers come in different sizes that all function roughly the same.

| Bits | Bytes | Signed C type | Unsigned C type      | Assembly |
|-----:|-------|---------------|----------------------|----------|
|    8 | 1     | `signed char` | `char`               | `byte`   |
|   16 | 2     | `short`       | `unsigned short`     | `word`   |
|   32 | 4     | `int`         | `unsigned int`       | `dword`  |
|   64 | 8     | `long long`   | `unsigned long long` | `qword`  |

The bits of an integer are simply stored sequentially, and the only ambiguity here is the order in which to store them — left to right or right to left — called *endianness*. Depending on the architecture, the format can be either:

- *Little-endian*, which lists *lower* bits first. For example, $42_{10}$ will be stored as $010101$.
- *Big-endian*, which lists *higher* bits first. All previous examples in this article follow it.

This seems like an important architecture aspect, but actually in most cases it doesn't make a difference: just pick one style and stick with it. But in some cases it does:

- Little-endian has the advantage that you can cast a value to a smaller type (e. g. `long long` to `int`) by just loading fewer bytes, which in most cases means doing nothing — thanks to *register aliasing*, `eax` refers to the first 4 bytes of `rax`, so conversion is essentially free. It is also easier to read values in a variety of type sizes — while on big-endian architectures, loading a `int` from a `long long` array would require shifting the pointer by 2 bytes.
- Big-endian has the advantage that higher bytes are loaded first, which in theory can make highest-to-lowest routines such as comparisons and printing faster. You can also perform certain checks such as finding out whether a number is negative by only loading its first byte.

Big-endian is also more "natural" — this is how we write binary numbers on paper — but the advantage of having faster type conversions outweigh it. For this reason, little-endian is used by default on most hardware, although some CPUs are "bi-endian" and can be configured to switch modes on demand.

### 128-bit Integers

Sometimes we need to multiply two 64-bit integers to get a 128-bit integer — that usually serves as a temporary value and e. g. reduced by modulo right away.

There are no 128-bit registers to hold the result of such multiplication, but `mul` instruction can operate in a manner [similar to division](/hpc/analyzing-performance/gcd/), by multiplying whatever is stored in `rax` by its operand and [writing the result](https://gcc.godbolt.org/z/4Gfxhs84Y) into two registers — the lower 64 bits of the result will go into `rdx`, and `rax` will have the higher 64 bits. Some languages have a special type to support such an operation:

```cpp
void prod(int64_t a, int64_t b, __int128 *c) {
    *c = a * (__int128) b;
}
```

For all purposes other than multiplication, 128-bit integers are just bundled as two registers. This makes it too weird to have a full-fledged 128-bit type, so the support for it is limited. The typical use for this type is to get either the lower or the higher part of the multiplication and forget about it:

```c++
__int128_t x = 1;
int64_t hi = x >> 64;
int64_t lo = (int64_t) x; // will be just truncated
```

Other platforms provide similar mechanisms for dealing with longer-than-word multiplication. For example, arm has `mulhi` and `mullo` instruction, returning lower and higher parts of the multiplication, and x86 SIMD extensions have similar 32-bit instructions.

## Integer Division

As we know from [the case study of GCD](/hpc/analyzing-performance/gcd/), integer division is painfully slow, even when fully implemented in hardware. Usually we want to avoid doing it in the first place, but when we can't, there are several clever tricks that replace it with multiplication at the cost of a bit of precomputation.

All these tricks are based on the following idea. Consider the task of dividing one floating-point number $x$ by another floating-point number $y$, when $y$ is known in advance. What we can do is to calculate a constant

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

This trick is called *Barrett reduction*, and it's called "reduction" because it is mostly used for modulo operations, which can be replaced with a single division, multiplication and subtraction by the virtue of this formula:

$$
r = x - \lfloor x / y \rfloor \cdot y
$$

This method requires some precomputation, including performing one actual division, so this is only beneficial when you do not one, but a few of them, with a constant divisor.

### Why It Works

It is not very clear why such $m$ and $s$ always exist, let alone how to find them. But given a fixed $s$, intuition tells us that $m$ should be as close to $2^s/y$ as possible for $2^s$ to cancel out. So there are two natural choices: $\lfloor 2^s/y \rfloor$ and $\lceil 2^s/y \rceil$. The first one doesn't work, because if you substitute

$$
\lfloor \frac{x \cdot \lfloor 2^s/y \rfloor}{2^s} \rfloor
$$

then for any integer $\frac{x}{y}$ where $y$ is not even, the result will be stricly less than the truth. This only leaves the other case, $m = \lceil 2^s/y \rceil$. Now, let's try to derive the lower and upper bounds for the result of the computation:

$$
  \lfloor x / y \rfloor
= \lfloor \frac{x \cdot m}{2^s} \rfloor
= \lfloor \frac{x \cdot \lceil  2^s /y \rceil}{2^s} \rfloor
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
\lfloor \frac{x \cdot \lceil  2^s /y \rceil}{2^s} \rfloor
<
x / y + x / 2^s
$$

We can see that the result falls somewhere in a range of size $(1 + \frac{x}{2^s})$, and if this range always has exactly one integer for all possible $x / y$, then the algorithm is guaranteed to give the right answer. Turns out, we can always set $s$ to be high enough to achieve it.

What will be the worst case here? How to pick $x$ and $y$ so that $(x/y - 1, x/y + x / 2^s)$ contains two integers? We can see that integer ratios don't work, because the left border is not included, and assuming $x/2^s < 1$, only $x/y$ itself will be in the range. The worst case is in actually the $x/y$ that comes closest to $1$ without exceeding it. For $n$-bit integers, that is the second largest possible integer divided by the first largest:

$$
\begin{aligned}
    x = 2^n - 2
\\  y = 2^n - 1
\end{aligned}
$$

In this case, the lower bound will be $(\frac{2^n-2}{2^n-1} - 1)$ and the upper bound will be $(\frac{2^n-2}{2^n-1} + \frac{2^n-2}{2^s})$. The left border is as close to a whole number as possible, and the size of the whole range is the second largest possible. And here is the punchline: if $s \ge n$, then the only integer contained in this range is $1$, and so the algorithm will always return it.

### Lemire Reduction

Barrett reduction is a bit complicated, and also generates a length instruction sequence for modulo because it is computed indirectly. There a new ([2019](https://arxiv.org/pdf/1902.01961.pdf)) method, which is simpler and actually faster for modulo in some cases. It doesn't have a conventional name yet, but I am going to refer to it as [Lemire](https://lemire.me/blog/) reduction.

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
= \lfloor \frac{x \cdot m}{2^s} \rfloor
= \lfloor \frac{x \cdot \lceil  2^s /y \rceil}{2^s} \rfloor
$$

What we really do here is we multiply $x$ by a floating-point constant ($x \cdot m$) and then truncate the result $(\lfloor \frac{\cdot}{2^s} \rfloor)$.

What if we took not the highest bits, but the lowest? This would correspond to the fractional part — and if we multiply it back by $y$ and truncate the result, this will be exactly the remainder:

$$
r = \Bigl \lfloor \frac{ (x \cdot \lceil  2^s /y \rceil \bmod 2^s) \cdot y }{2^s} \Bigr \rfloor
$$

This works perfectly, because what we do here can be interpreted as just three chained floating-point multiplications with the total relative error of $O(\epsilon)$. Since $\epsilon = O(\frac{1}{2^s})$ and $s = 2n$, the error will always be less than one, and hence the result will be exact.

```c++
uint32_t y;

uint64_t m = uint64_t(-1) / y + 1; // ceil(2^64 / d)

uint32_t mod(uint32_t x) {
    uint64_t lowbits = m * x;
    return ((__uint128_t) lowbits * y) >> 64; 
}

uint32_t div(uint32_t x) {
    return ((__uint128_t) m * x) >> 64;
}
```

The only downside of this method is that it needs integer types four times the original size to perform the multiplication, while other reduction methods can work with just the double.

There is a a way though to compute 64x64 modulo by carefully manipulating the halves of intermediate results; the implementation is left as an exercise to the reader.
