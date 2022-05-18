---
title: Floating-Point Numbers
weight: 1
---

The users of floating-point arithmetic deserve one of these IQ bell curve memes — because this is how the relationship between it and most people typically proceeds:

- Beginner programmers use it everywhere as if it was some magic unlimited-precision data type.
- Then they discover that `0.1 + 0.2 != 0.3` or some other quirk like that, freak out, start thinking that some random error term is added to every computation, and for many years avoid any real data types completely.
- Then they finally man up, read the specification of how IEEE-754 floats work and start using them appropriately.

Unfortunately, too many people are still at stage 2, breeding various misconceptions about floating-point arithmetic — thinking that it is fundamentally imprecise and unstable, and slower than integer arithmetic.

![](../img/iq.svg)

But these are all just myths. Floating-point arithmetic is often *faster* than integer arithmetic because of specialized instructions, and real number representations are thoroughly standardized and follow simple and deterministic rules in terms of rounding, allowing you to manage computational errors reliably.

In fact, it is so reliable that some high-level programming languages, most notably JavaScript, don't have integers at all. In JavaScript, there is only one `number` type, which is internally stored as a 64-bit `double`, and due to the way floating-point arithmetic works, all integer numbers between $-2^{53}$ and $2^{53}$ and results of computations involving them can be stored exactly, so from a programmer's perspective, there is little practical need for a separate integer type.

One notable exception is when you need to perform bitwise operations with numbers, which *floating-point units* (the coprocessors responsible for operations on floating-point numbers) typically don't support. In this case, they need to be converted to integers, which is so frequently used in JavaScript-enabled browsers that arm [added a special "FJCVTZS" instruction](https://community.arm.com/developer/ip-products/processors/b/processors-ip-blog/posts/armv8-a-architecture-2016-additions) that stands for "Floating-point Javascript Convert to Signed fixed-point, rounding toward Zero" and does what it says it does — converts real to integer the exact same way as JavaScript — which is an interesting example of the software-hardware feedback loop in action.

But unless you are a JavaScript developer who uses real types exclusively to emulate integer arithmetic, you probably need a more in-depth guide about floating-point arithmetic, so we are going to start with a broader subject.

## Real Number Representations

If you need to deal with real (non-integer) numbers, you have several options with varying applicability. Before jumping straight to floating-point numbers, which is what most of this article is about, we want to discuss the available alternatives and the motivation behind them — after all, people who avoid floating-point arithmetic do have a point.

### Symbolic Expressions

The first and the most cumbersome approach is to store not the resulting values themselves but the algebraic expressions that produce them.

Here is a simple example. In some applications, such as computational geometry, apart from adding, subtracting and multiplying numbers, you also need to divide without rounding, producing a rational number, which can be exactly represented with a ratio of two integers:

```c++
struct r {
    int x, y;
};

r operator+(r a, r b) { return {a.x * b.y + a.y * b.x, a.y * b.y}; }
r operator*(r a, r b) { return {a.x * b.x, a.y * b.y}; }
r operator/(r a, r b) { return {a.x * b.x, a.y * b.y}; }
bool operator<(r a, r b) { return a.x * b.y < b.x * a.y; }
// ...and so on, you get the idea
```

This ratio can be made irreducible, which would even make this representation unique:

```c++
struct r {
    int x, y;
    r(int x, int y) : x(x), y(y) {
        if (y < 0)
            x = -x, y = -y;
        int g = gcd(x, y);
        x /= g;
        y /= g;
    }
};
```

This is how *computer algebra* systems such as WolframAlpha and SageMath work: they operate solely on symbolic expressions and avoid evaluating anything as real values.

With this method, you get absolute precision, and it works well when you have a limited scope such as only supporting rational numbers. But this comes at a large computational cost because in general, you would need to somehow store the whole history of operations that led to the result and take it into account each time you perform a new operation — which quickly becomes unfeasible as the history grows.

### Fixed-Point Numbers

Another approach is to stick to integers, but treat them as if they were multiplied by a fixed constant. This is essentially the same as changing units of measurement for more up-to-scale ones.

Because some values can't be represented exactly, this makes computations imprecise: you need to round the results to nearest representable value.

This approach is commonly used in financial software, where you *really* need a straightforward way to manage rounding errors so that the final numbers add up. For example, NASDAQ uses $\frac{1}{10000}$-th of a dollar as its base unit in its stock listings, meaning that you get the precision of exactly 4 digits after comma in all transactions.

```c++
struct money {
    uint v; // 1/10000th of a dollar
};

std::string to_string(money) {
    return std::format("${0}.{1:04d}", v / 10000, v % 10000);
}

money operator*(money x, money y) { return {x.v * y.v / 10000}; }
```

Apart from introducing rounding errors, a bigger problem is that they become useless when the scaling constant is misplaced. If the numbers you are working with are too large, then the internal integer value will overflow, and if the numbers are too small, they will be just rounded down to zero. Interestingly, the former case once [became an issue](https://www.wsj.com/articles/berkshire-hathaways-stock-price-is-too-much-for-computers-11620168548) on NASDAQ when the Berkshire Hathaway stock price approached $\frac{2^{32} - 1}{10000}$ = $429,496.7295 and could no longer fit in an unsigned 32-bit integer.

This problem makes fixed-point arithmetic fundamentally unsuitable for applications where you need to use both small and large numbers, for example, evaluating certain physics equations:

$$
E = m c^2
$$

In this particular one, $m$ is typically of the same order of magnitude as the mass of a proton ($1.67 \cdot 10^{-27}$ kg) and $c$ is the speed of light ($3 \cdot 10^9$ m/s).

### Floating-Point Numbers

In most numerical applications, we are mainly concerned with the relative error. We want the result of our computations to differ from the truth by no more than, say, $0.01\\%$, and we don't really care what that $0.01\\%$ equates to in absolute units.

Floating-point numbers solve this by storing a certain number of the most significant digits and the order of magnitude of the number. More precisely, they are represented with an integer (called *significand* or *mantissa*) and scaled using an exponent of some fixed base — most commonly, 2 or 10. For example:

$$
1.2345 =
\underbrace{12345}_\text{mantissa}
\times {\underbrace{10}_\text{base}\!\!\!\!}
      ^{\overbrace{-4}^\text{exponent}}
$$

Computers operate on fixed-length binary words, so when designing a floating-point format for hardware, you'd want a fixed-length binary format where some bits are dedicated for the mantissa (for more precision) and some for the exponent (for more range).

This handmade float implementation hopefully conveys the idea:

```cpp
// DIY floating-point number
struct fp {
    int m; // mantissa
    int e; // exponent
};
```

This way we can represent numbers in the form $\pm \\; m \times 2^e$ where both $m$ and $e$ are bounded *and possibly negative* integers — which would correspond to negative or small numbers respectively. The distribution of these numbers is very much non-uniform: there are roughly as many numbers in the $[0, 1)$ range as in the $[1, +\infty)$ range.

Note that these representations are not unique for some numbers. For example, number $1$ can be represented as

$$
1 \times 2^0 = 2 \times 2^{-1} = 256 \times 2^{-8}
$$

and in 28 other ways that don't overflow the mantissa.

This can be problematic for some applications, such as comparisons or hashing. To fix this, we can *normalize* these representations using a certain convention. In decimal, the [standard form](https://en.wikipedia.org/wiki/Scientific_notation) is to always put the comma after the first digit (`6.022e23`), and for binary, we can do the same:

$$
42 = 10101_2 = 1.0101_2 \times 2^5
$$

Notice that, following this rule, the first bit is always 1. It is redundant to store it explicitly, so we will just pretend that it's there and only store the other bits, which correspond to some rational number in the $[0, 1)$ range. The set of representable numbers is now roughly

$$
\{ \pm \; (1 + m) \cdot 2^e \; | \; m = \frac{x}{2^{32}}, \; x \in [0, 2^{32}) \}
$$

Since $m$ is now a nonnegative value, we will now make it unsigned integer, and instead add a separate Boolean field for the sign of the number:

```cpp
struct fp {
    bool s;     // sign: "0" for "+", "1" for "-" 
    unsigned m; // mantissa
    int e;      // exponent
};
```

Now, let's try to implement some arithmetic operation — for example, multiplication — using our handmade floats. Using the new formula, the result should be:

$$
\begin{aligned}
c  &= a \cdot b
\\ &= (s_a \cdot (1 + m_a) \cdot 2^{e_a}) \cdot (s_b \cdot (1 + m_b) \cdot 2^{e_b})
\\ &= s_a \cdot s_b \cdot (1 + m_a) \cdot (1 + m_b) \cdot 2^{e_a} \cdot 2^{e_b} 
\\ &= \underbrace{s_a \cdot s_b}_{s_c} \cdot (1 + \underbrace{m_a + m_b + m_a \cdot m_b}_{m_c}) \cdot 2^{\overbrace{e_a + e_b}^{e_c}}
\end{aligned}
$$

The groupings now seem straightforward to calculate, but there are two nuances:

- The new mantissa is now in the $[0, 3)$ range. We need to check if it is larger than $1$ and normalize the representation, applying the following formula: $1 + m = (1 + 1) + (m - 1) = (1 + \frac{m - 1}{2}) \cdot 2$.
- The resulting number can be (and very likely is) not representable exactly due to the lack of precision. We need twice as many bits to account for the $m_a \cdot m_b$ term, and the best we can do here is to round it to the nearest representable number.

Since we need some extra bits to properly handle the mantissa overflow issue, we will reserve one bit from $m$ thus limiting it to $[0,2^{31})$ range. 

```c++
fp operator*(fp a, fp b) {
    fp c;
    c.s = a.s ^ b.s;
    c.e = a.e + b.e;
    
    uint64_t x = a.m, y = b.m; // casting to wider types
    uint64_t m = (x << 31) + (y << 31) + x * y; // 62- or 63-bit intermediate result
    if (m & (1<<62)) { // checking for overflow
        m -= (1<<62); // m -= 1;
        m >>= 1;
        c.e++;
    }
    m += (1<<30); // "rounding" by adding 0.5 to a value that will be floored next
    c.m = m >> 31;
    
    return c;
}
```

Many applications that require higher levels of precision use software floating-point arithmetic in a similar fashion. But of course, you don't want to execute a sequence of 10 or so instructions that this code compiles to each time you want to multiply two real numbers, so on modern CPUs, floating-point arithmetic is implemented in hardware — usually as separate coprocessors due to its complexity.

The *floating-point unit* of x86 (often referred to as x87) has separate registers and its own tiny instruction set that supports memory operations, basic arithmetic, trigonometry, and some common operations such as logarithm, exponent, and square root. To make these operations properly work together, some additional details of floating-point number representation need to be clarified — which we will do in [the next section](../ieee-754).
