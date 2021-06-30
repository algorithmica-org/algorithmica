---
title: Integer Arithmetic
weight: 3
---

If you read this chapted from the beginning, you must be wondering: why would it introduce integer arithmetic after floating-point one?

The reason is that, while plain integers are simpler, but counterintuitively, their elequent simplicity allows for more possibilities for operations to be expressed by buiding blocks of other. If floating-point representation is so unwieldy that most of its operations are implemented in hardware, operating integers they require a much more creative use of the instruction set.

## Binary Formats

Unsigned integers are indeed very simple: they are just natural values written in binary.

You can't work with individual bits because that's how memory system works. Byte is the smallest. There is no such thing as "signed byte".

When the result can't fit into the word, it "overflows" — or "underflows" if it would be a negative value — by truncating to the last wordsize bits of the result. It raises a special flag which you can check, but usually when people are explicitly using unsigned integers the overflow is a very much desired feature.

### Endianness

The only confusing part about unsigned integers is whether to store their bits left to right or right to left. This isn't much of an issue: just pick one and stick with it, but sometimes it matters, especially when you alias numbers.

Pick an arbitrary side, what's wrong if electrons end up to have "-" sign which actually means more electrons? Just a little bit of confusion.

Little-endianness is the dominant ordering for processor architectures. You need to be able to down-cast a type (say, from `int` to `short`) and keep the pointers. Same thing with register aliasing: you want to refer to lower part of a value, and it makes more sense for it to be the first half.

So big endian seems natural because that's how we write numbers, but there are natural reasons to use little endian (lowest bits first), so this is what we use.

Some architectures are bi-endian for compatibility reasons, meaning that they can switch modes, while some others have fast instruction for value conversion.

Disadvantages:

- Most significant bytes come first, and in theory comparisons can be done faster (also, if you are looking for negative values, you can just fetch upper byte)

https://uynguyen.github.io/2018/04/30/Big-Endian-vs-Little-Endian/#:~:text=The%20advantages%20of%20Little%20Endian,32%2C%2064%2Dbit%20reads.

### Two's Complement

When you are doing engineering, laziness is a virtue. In computer engineering, this means saving transistor space by reusing circuitry that you already have for other operation.

This is the principle that people followed when designing signed integer format. Let's assume that numbers in range $[0, 2^{n-1})$ will remain what they are and we don't have to convert them. For other numbers, let's pretend like they are "overflowing" and start from $2^{-31}$. This is actually how it is implemented in hardware: with the same circuitry except that the overflow flag is now triggered one position to the left.

$$
-x = 2^{32} - x
-x = ~x + 1
$$

There is one more negative number than there is positive numbers, because zero has $0$ sign bit.

This is how they behave in most hardware, although languages leave some leeway and assume that signed integers never overflow (C++ interprets it as undefined behavior), so you should always use unsigned integers when you expect overflows so that compiler doesn't do some incorrect optimizations. Some languages very much encourage unsigned types.

### 128-bit Integers

Sometimes we need to multiply two 64-bit integers to get a 128-bit integer — usually to serve as a temporary value, e. g. to be reduced by modulo right away. The `mul` instruction can act in a maner similar to division: you place a value at a specified register and call `mul` without arguments. The result will be stored in `rdx` (lower 64 bits) and `rax` (higher 64 bits).

For all operations other than multiplication, 128-bit integers are just bundled as two registers. This makes it too weird to have a separate 128-bit types in higher-level languages, but some compilers implement some kind of way to use it anyway:

```c++
__int128_t x = 1;
int64_t hi = x >> 64;
int64_t lo = (int64_t) x; // will just be trunkated
```

You can't print them. Also, modulo and many other operations will call a separate very slow library.

Other platforms provide similar mechanisms for dealing with longer-than-word multiplication. ARM has `mulhi` and `mullo`, x86 SIMD extensions have similar, but 32-bit instruction.

### Integer Division

As we know from binary GCD, integer division is painfully slow, even when implemented fully in hardware. When we can't avoid doing it in the first place, there are clever tricks that replace it with multiplication at the cost of a little bit of precomputation.

All fast division tricks are based on the following idea. Consider the problem when we need to divide one floating-point number $x$ by another floating-point number $y$ known in advance. What we can do is to calculate a constant $d = y^{-1}$ and during runtime calculate $x / y = x \cdot x^{-1} \approx x \cdot d$. The result of $\frac{1}{y}$ will be at most $\epsilon$ off, so the result of $x \cdot d$ will be at most $\epsilon$ off too, which is tolerable.

When switching to integers, this $\epsilon$ may be an issue, because we need precision, expeciall when calculating modulo operations. It is harder: you need to replace division with a multiplication and a binary shift. For it all to be exact, you need to approximate $\frac{1}{d} \approx \frac{m}{2^s}$ by adding a "magic" number $m$ picking a power of two $s$ such that `x / d == (x * m) >> s` for all `x`. It can be shown that such a pair always exists, and compilers perform an optimization like that themselves every time they encouncer a division by a constant. Here are the generated assembly for dividing an `unsigned long long` by $10^9 + 7$:

```nasm
movq    %rdi, %rax
movabsq $-8543223828751151131, %rdx ; load magic constant into a register
mulq    %rdx                        ; perform multiplication
movq    %rdx, %rax
shrq    $29, %rax                   ; binary shift of the result
```

Calculating modulo can be done by division and then multiplication and substraction by the virtue of formula $r = x - \lfloor x / y \rfloor \cdot y $.

This is called Barrett reduction, and honestly I think my mental health deteriorated a little bit when I was going through formal proofs. But there is a simpler method, which is also faster for calculating modulo. It is pretty new (2019) and doesn't have a conventional name, but I am going to call it Lemire reduction. Consider the bits of the result:

$$
...
$$

The bits before the dot represent the dividend. The bits after the dot represent remainder (which is divided by $y$, so you need to multiply it back). Since the relative error is at most $\epsilon$, having twice as many digits always works.

```c++
uint64_t c = uint64_t(-1) / d + 1; // ceil(2^64 / d)

uint64_t mod(uint32_t n, uint32_t d) {
    uint64_t lowbits = c * n;
    uint64_t res = ((__uint128_t) lowbits * d) >> 64; 

    return res;
}

uint64_t div(uint32_t n, uint32_t d) {
    uint64_t res = ((__uint128_t) c * n) >> 64;

    return res;
}
```

Modulo.
