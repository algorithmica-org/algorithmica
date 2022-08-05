---
title: Integer Numbers
weight: 5
---

If you are reading this chapter sequentially from the beginning, you might be wondering: why would I introduce integer arithmetic after floating-point one? Isn't it supposed to be easier?

True: plain integer representations are simpler. But, counterintuitively, their simplicity allows for more possibilities for operations to be expressed in terms of others. And if floating-point representations are so unwieldy that most of their operations are implemented in hardware, efficiently manipulating integers requires much more creative use of the instruction set.

## Binary Formats

*Unsigned integers* are just natural numbers written in binary:

$$
\begin{aligned}
   5_{10}   &= 101_2 = 4 + 1
\\ 42_{10}  &= 101010_2 = 32 + 8 + 2
\\ 256_{10} &= 100000000_2 = 2^8
\end{aligned}
$$

When the result of an operation can't fit into the word size (e.g., is more or equal to $2^{32}$ for 32-bit unsigned integers), it *overflows* by leaving only the lowest 32 bits of the result. Similarly, if the result is a negative value, it *underflows* by adding it to $2^{32}$, so that it always stays in the $[0, 2^{32})$ range.

This is equivalent to performing all operations modulo a power of two:

$$
\begin{aligned}
    256                 &\equiv 0 \pmod {2^8}
\\  2021                &\equiv 229 \pmod {2^8}
\\  -42 \equiv 256 - 42 &\equiv 214 \pmod {2^8}
\end{aligned}
$$

In either case, it raises a special flag which you can check, but usually when people explicitly use unsigned integers, they are expecting this behavior.

### Signed Integers

*Signed integers* support storing negative values by dedicating the highest bit to represent the sign of the number, in a similar fashion as floating-point numbers do. This halves the range of representable non-negative numbers: the maximum possible 32-bit integer is now $(2^{31}-1)$ and not $(2^{32}-1)$. But the encoding of negative values is not quite the same as for floating-point numbers.

Computer engineers are even lazier than programmers — and this is not only motivated by the instinctive desire for simplification, but also by saving transistor space. This can be achieved by reusing circuitry that you already have for other operations, which is what they aimed for when designing the signed integer format:

- For an $n$-bit signed integer type, the encodings of all numbers in the $[0, 2^{n-1})$ range remain the same as their unsigned binary representations.
- All numbers in the $[-2^{n-1}, 0)$ range are encoded sequentially right after the "positive" range — that is, starting with $(-2^{n - 1})$ that has code $(2^{n-1})$ and ending with $(-1)$ that has code $(2^n - 1)$.

One way to look at this is that all negative numbers are just encoded as if they were subtracted from $2^n$ — an operation known as *two's complement*:

$$
\begin{aligned}
-x &= 2^{32} - x
\\ &= \bar{x} + 1
\end{aligned}
$$

Here $\bar{x}$ represents bitwise negation, which can be also thought of as subtracting $x$ from $(2^n - 1)$.

As an exercise, here are some facts about signed integers:

- All positive numbers and zero remain the same as their binary notation.
- All negative numbers have the highest bit set to one.
- There are more negative numbers than positive numbers (exactly by one — because of zero).
- For `int`, if you add $1$ to $(2^{31}-1)$, the result will be $-2^{31}$, represented as `10000000` (for exposition purposes, we will only write 8 bits instead of 32).
- Knowing a binary notation of a positive number `x`, you can get the binary notation of `-x` as `~x + 1`.
- `-1` is represented as `~1 + 1 = 11111110 + 00000001 = 11111111`.
- `-42` is represented as `~42 + 1 = 11010101 + 00000001 = 11010110`.
- The number `-1 = 11111111` is followed by `0 = -1 + 1 = 11111111 + 00000001 = 00000000`.

The main advantage of this encoding is that you don't have to do anything to convert unsigned integers to signed ones (except maybe check for overflow), and you can reuse the same circuitry for most operations, possibly only flipping the sign bit for comparisons and such.

That said, you need to be careful with signed integer overflows. Even though they almost always overflow the same way as unsigned integers, programming languages usually consider the possibility of overflow as undefined behavior. If you need to overflow integer variables, convert them to unsigned integers: it's free anyway.

**Exercise.** What is the only integer value for which `std::abs` produces a wrong result? What will this result be?

### Integer Types

Integers come in different sizes, but all function roughly the same.

| Bits | Bytes | Signed C type        | Unsigned C type      | Assembly |
|-----:|-------|----------------------|----------------------|----------|
|    8 | 1     | `signed char`[^char] | `unsigned char`      | `byte`   |
|   16 | 2     | `short`              | `unsigned short`     | `word`   |
|   32 | 4     | `int`                | `unsigned int`       | `dword`  |
|   64 | 8     | `long long`          | `unsigned long long` | `qword`  |

[^char]: Note that `char`, `unsigned char`, and `signed char` are technically three distinct types. The C standard leaves it up to the implementation whether the plain `char` is signed or unsigned (on most compilers, it is signed).

The bits of an integer are simply stored sequentially. The only ambiguity here is the order in which to store them — left to right or right to left — called *endianness*. Depending on the architecture, the format can be either:

- *Little-endian*, which lists *lower* bits first. For example, $42_{10}$ will be stored as $010101$.
- *Big-endian*, which lists *higher* bits first. All previous examples in this article follow it.

This seems like an important architecture aspect, but in most cases, it doesn't make a difference: just pick one style and stick with it. But in some cases it does:

- Little-endian has the advantage that you can cast a value to a smaller type (e.g., `long long` to `int`) by just loading fewer bytes, which in most cases means doing nothing — thanks to *register aliasing*, `eax` refers to the first 4 bytes of `rax`, so conversion is essentially free. It is also easier to read values in a variety of type sizes — while on big-endian architectures, loading an `int` from a `long long` array would require shifting the pointer by 2 bytes.
- Big-endian has the advantage that higher bytes are loaded first, which in theory can make highest-to-lowest routines such as comparisons and printing faster. You can also perform certain checks such as finding out whether a number is negative by only loading its first byte.

Big-endian is also more "natural" — this is how we write binary numbers on paper — but the advantage of having faster type conversions outweights it. For this reason, little-endian is used by default on most hardware, although some CPUs are "bi-endian" and can be configured to switch modes on demand.

### 128-bit Integers

Sometimes we need to multiply two 64-bit integers to get a 128-bit integer — usually to serve as a temporary value and be reduced modulo a 64-bit integer right away.

There are no 128-bit registers to hold the result of such multiplication, so the `mul` instruction, in addition to the normal `mul r r` form where it multiplies the values in registers and keeps the lower half of the result, has another `mul r` mode, where it multiplies whatever is stored in the `rax` register by its operand, and writes the result into two registers — the lower 64 bits of the result will go into `rax`, and the higher 64 bits go into `rdx`:

```nasm
; input: 64-bit integers a and b, stored in rsi and rdi
; output: 128-bit product a * b, stored in rax (lower 64-bit) and rdx (higher 64-bit)
mov     rax, rdi
mov     r8, rdx
imul    rsi
```

Some compilers have a separate type supporting this operation. In GCC and Clang it is available as `__int128`:

```cpp
void prod(int64_t a, int64_t b, __int128 *c) {
    *c = a * (__int128) b;
}
```

Its typical use case is to immediately extract either the lower or the higher part of the multiplication and forget about it:

```c++
__int128_t x = 1;
int64_t hi = x >> 64;
int64_t lo = (int64_t) x; // will be just truncated
```

For all purposes other than multiplication, 128-bit integers are just bundled as two registers. This makes it too weird to have a full-fledged 128-bit type, so the support for it is limited, other than for basic arithmetic operations. For example:

```c++
__int128_t add(__int128_t a, __int128_t b) {
    return a + b;
}
```

is compiled into:

```nasm
add:
    mov rax, rdi
    add rax, rdx    ; this sets the carry flag in case of an overflow
    adc rsi, rcx    ; +1 if the carry flag is set
    mov rdx, rsi
    ret
```

Other platforms provide similar mechanisms for dealing with longer-than-word multiplication. For example, Arm has `mulhi` and `mullo` instructions, returning lower and higher parts of the multiplication, and x86 [SIMD extensions](/hpc/simd) have similar 32-bit instructions.
