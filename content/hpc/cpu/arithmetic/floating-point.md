---
title: Floating-Point Arithmetic
weight: 1
---

Floating-point arithmetic is treated as a bit of an esoteric subject in computer science curricula. Given the widespread use of numerical algorithms, this is rather surprising that there are still so many prevalent misconceptions about it. Most programmers think that it is slower than integer arithmetic, fundamentally imprecise and unstable, and that a random error term is added to the result every computation involving floating-point types, and therefore just tend to avoid it altogether.

But these are all just myths. Floating-point arithmetic is often even faster than integer one due to the availability of specialized instructions, and floating-point representations are thoroughly standartized and follow simple and well-defined rules for rounding, so that you *can* reliably manage errors and even perform some computations exactly.

## Real Number Representations

If you need to deal with real (non-integer) numbers, you have several options with varying applicability. Before jumping straight to floating-point numbers, which is what most of this section is about, we want first to discuss the available alternatives and the motivation behind them.

The people who avoid floating-point number do have a point, so let's discuss first what we can do without them when we deal with non-integer data.

### Symbolic Expressions

The first and the most cumbersome approach is to store not the resulting values themselves, but the algebraic expressions that produce them.

Here is a simple example. In some applications, such as computational geometry, apart from addding, subtracting and multiplying numbers, you also need to divide without rounding, producing a rational number, which can be exactly represented with a ratio of two integers:

```c++
struct r {
    int x, y;
};

r operator+(r a, r b) { return r{a.x * b.y + a.y * b.x, a.y * b.y}; }
r operator*(r a, r b) { return r{a.x * b.x, a.y * b.y}; }
r operator/(r a, r b) { return r{a.x * b.x, a.y * b.y}; }
bool operator<(r a, r b) { return a.x * b.y < b.x * a.y; }
// ...and so on, you get the idea
```

This ratio can also be made irreducible, which would also make this representation unique:

```c++
struct r {
    int x, y;
    r(int x, int y) : x(x), y(y) {
        int g = gcd(x, y);
        x /= g;
        y /= g;
    }
};
```

This is how computer algebra systems such as WolframAlpha and SageMath work: they operate solely on symbolic expressions and avoid evaluating anything as real values.

You get absolute precision with this method, and it works well when you have a limited scope such as only supporting rational numbers. But this comes at a large computational cost because in general you would need to somehow store the whole history of operations that led to the result and take them into account when every time you perform new operations.

### Fixed-Point Numbers

Another approach is to stick to integers, but pretend like they are multiplied by a certain constant. This is the same as changing units of measurement.

Due to inability to represent some values exactly, this makes computations imprecise: when this happens, you need to round it the to nearest representable value.

This approach is also commonly used in financial software, where you really need a straightforward way to round errors so that final numbers add up. For example, NASDAQ uses $\frac{1}{10000}$-th of a dollar as its base unit in its stock listings, meaning that you get precision of exactly 4 digits after comma in all transactions.

```c++
struct money {
    uint v; // 1/10000th of a dollar
};

std::string to_string(money) {
	return std::format("${0}.{1:04d}", v / 10000, v % 10000);
}

money operator*(money x, money y) { return {x.v * y.v / 10000}; }
```

Apart from introducing rounding errors, a bigger problem is that they become useless when the scaling constant is misplaced: if the numbers you are really working with are too large, then the internal store will overflow, and if the numbers are too small, they will be just rounded down to zero. Interestingly, the former once [became an issue](https://www.wsj.com/articles/berkshire-hathaways-stock-price-is-too-much-for-computers-11620168548) on NASDAQ when the price of a stock came close to $\frac{2^{32} - 1}{10000}$ = $429,496.7295 and could no longer fit in an unsigned 32-bit integer.

This problem makes them fundamentally unsuitable for applications where you need to use both small and large numbers, like evaluating some physics equations:

$$
E = m c^2
$$

Here, $m$ is of the same order of magnitude as the mass of a proton ($1.67 \cdot 10^{-27}$ kg) and $c$ is the speed of light ($3 \cdot 10^9$ m/s).

### Floating-Point Numbers

In most numerical applications, we are mainly concerned with the relative error. We want the result of our computations to differ from the truth by no more than, say, $0.01\\%$, and we don't really care what that $0.01\\%$ equates to in absolute units.

Floating-point numbers solve this by storing a fixed number of the most significant digits and the order of magnitude of the number. More precisely, they are represented with an integer (called *significand* or *mantissa*) and scaled using an exponent of some fixed base (most commonly, 2 or 10). For example:

$$
1.2345 =
\underbrace{12345}\_\text{mantissa}
\times {\underbrace{10}\_\text{base}\\!\\!\\!\\!}
      ^{\overbrace{-4}^\text{exponent}}
$$

Computers work with binary words, so you want a fixed length binary format where some bits are dedicated for the mantissa (for more precision) and some for the exponent (for more range). You also need to spend two extra bits to support negative numbers (with "negative mantissa") and small numbers (with "negative exponent").

The following handmade float implementation conveys the idea:

```c++
// DIY floating-point number
struct fp {
    int m; // mantissa
    int e; // exponent
};
```

This way we can represent numbers in the form $\pm \\; m \times 2^e$ where both $m$ and $e$ are bounded integers, but it has an issue that these representations are not unique for some numbers. For example, number $1$ can be represented as $1 \times 2^0$, $2 \times 2^{-1}$, $256 \times 2^{-8}$ and in 28 other ways that don't overflow the mantissa. This can be problematic for some applications, such as comparisons or hashing.

To fix this, we can *normalize* these representations using a certain convention. In decimal, the [standard form](https://en.wikipedia.org/wiki/Scientific_notation) is to always put the comma after the first digit (`6.022e23`) and in binary we can do the same:

$$
42 = 10101_2 = 1.0101_2 \times 2^5
$$

Notice that, following this rule, the first bit is always 1. It is redundant to store it explicitly, so we will just pretend that it's there and only store the other bits, which correspond to some number in the $[0, 1)$ range. The set of representable numbers now is roughly $\\{ \pm \\; (1 + m) \cdot 2^e \\; | \\; m \in [0, 1) \\}$.

Since $m$ is now a nonnegative number, we will now make it unsigned integer, and instead add a separate boolean field for the sign:

```c++
struct fp {
    bool s;     // sign: "0" for "+", "1" for "-" 
    unsigned m; // mantissa
    int e;      // exponent
};
```

The distribution of these numbers is not even. There are as many numbers in $[0, 1]$ range as in $[0, +\infty)$ range.

Now, let's try to implement some arithmetic operation — for example, multiplication — using our handmade floats. Using the new formula, the result will be:

$$
\begin{aligned}
c = a \cdot b &= (s_a \cdot (1 + m_a) \cdot 2^{e_a}) \cdot (s_b \cdot (1 + m_b) \cdot 2^{e_b})
\\\           &= s_a \cdot s_b \cdot (1 + m_a) \cdot (1 + m_b) \cdot 2^{e_a} \cdot 2^{e_b} 
\\\           &= \underbrace{s_a \cdot s_b}_{s_c} \cdot (1 + \underbrace{m_a + m_b + m_a \cdot m_b}\_{m_c}) \cdot 2^{\overbrace{e_a + e_b}^{e_c}}
\end{aligned}
$$

The groupings now seem straightforward to calculate, but there are two caveats:

1. The new mantissa is now in the $[0, 3)$ range. We need to check if it is larger than $1$ and normalize the representation, applying the following formula: $1 + m = (1 + 1) + (m - 1) = (1 + \frac{m - 1}{2}) \cdot 2$.
2. The resulting number can be (and very likely is) not representable exactly due to the lack of precision. We need twice as many bits to account for the $m_a \cdot m_b$ term, and the best we can do here is to round it to the nearest representable number.

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

Many applications that require higher precision use software floating-point arithmetic in a similar fashion. Buf of course, you don't want to execute a sequence 10 or so instructions that this code compiles to each time you want to multiply two real numbers, so floating-point arithmetic is implemented in hardware — often in separate coprocessors called floating-point units (FPU) due to its complexity. In x86, the FPU (often referred to as x87) has separate registers and its own tiny instruction set that supports memory operations, basic arithmetic, trigonometry and some common operations such logarithm, exponent and square root.

## IEEE 754 Floats

When we designed our DIY floating-point type, we disregarded quite a lot of corner cases and details:

- How many bits do we dedicate for the mantissa and the exponent?
- Does "0" sign bit means "+" or is it the other way around?
- How are these bits stored in memory?
- How do we represent 0?
- How exactly does rounding happen?
- What happens if we divide by zero?
- What happens if we take a square root of a negative number?
- What happens if increment the largest representable number?
- Can we somehow detect if one of the above 3 happened?

Most of the early computers didn't have floating-point arithmetic, and when vendors started adding floating-point coprocessors, they had slightly different vision for what answers to those questions should be. Diverse implementations made it difficult to use floating-point arithmetic reliably and portably — particularily for people develiping compilers for high-level langauges.

In 1985, Institute of Electrical and Electronics Engineers published a standard (called [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754)) that provided a formal specification of how floating-point numbers should work, which was then quickly adopted by the vendors and is now used by virtually all general-purpose computers.

IEEE 754 and further standards that build upon it define several floating-point representations. They all work roughly the same way as our handmade floats, but they differ in sizes. For example, the standard 32-bit `float` uses the first (highest) bit for sign, the next 8 bits for the exponent, and the 23 remaining bits for the mantissa:

![](../img/float.svg)

Apparently, they are stored in this exact order so that you can compare and sort them more quickly (in fact, if you flip the sign bit, you can use the same circuit as for integers).

You can go to this [online converter](https://www.h-schmidt.net/FloatConverter/IEEE754.html) if you want to play with it.

### Other Floats

There are other standard formats, depending on your use case:

* single: 1 sign, 8 exponent, 23 mantisssa
* double: 1 sign, 11 exponent, 52 mantissa
* half: 1 sign, 5 exponent, 10 mantissa
* extended: 15 exponent, 64 mantissa
* quad: 15 exponent, 112 mantissa
* bfloat16: 8 exponent, 7 mantissa

For some applications, it is so critical that manufacturers create a separate hardware or at least an instruction that supports these types.

For example, you don't need a lot of precision for machine learning (since input is noisy, why wouldn't computations be noisy too?), and most of it consists of matrix multiplications. Google has created a custom chip called TPU (tensor processing unit) that works with bfloat, and NVIDIA added "tensor cores" capable of doing 4x4 matrix multiplication in one go, but only for a specific data type.

There are also 40- and 80-bit types. `long double`

Higher precision types need more memory bandwidth and usually take more cycles to finish (e. g. division takes x, y, and z cycles depending on type).

### Special Values

* overflow or divide by zero: $\pm \infty$

invalid operations produce NaN

Overflow, underflow, division by zero, invalid, inexact

+-INF, +-NAN, +-zero

NAN propagates and raises flags and exceptions

In floating-point numbers, `-0` is not the same as `+0`.

This leaves an awkward exception for 0 and -0.

### Rounding

The way rounding works in hardware floats is actually remarkably simple: it occurs if (and *only* if) the result of the operation is not exact, and in this case it by default gets rounded to the nearest representable number (and to the nearest even digit in case of a tie).

Apart from the default mode (also known as Banker's rounding), you can [set](https://www.cplusplus.com/reference/cfenv/fesetround/) other rounding logic with 4 more modes:

* round to nearest, where ties round away from zero
* round up (toward $+\infty$; negative results thus round toward zero)
* round down (toward $-\infty$; negative results thus round away from zero)
* round toward zero (truncation)

The alternative rounding modes are also useful in diagnosing numerical instability: if the results of a subroutine vary substantially between rounding to + and − infinity then it is likely numerically unstable and affected by round-off error.

One could argue that rounding to nearest gives "expected" value the same given enough averaging, so changing rounding modes to estimate bounds is a better test than switching to a lower precision and checking whether the result changed by too much.

Statistically, half of the time they are rounding up and the other are rounding down, so they cancel each other.

It seems surprising to expect it from a hardware that calculates natural logarithms and square roots, but that's it: you get the highest precision possible from all operations. This makes it easy to analyze the errors, as we will see in a bit.

## Measuring and Mitigating Errors

It is worth to note that JavaScript uses the property that all operations are exact as long as the result is representable, and only uses floating-point numbers. There are not integers in JavaScript: only `double`, which have 53 bits of precision. The only exception is when you need to do bitwise operations with these numbers, which floating-point units don't support. In this case, they are converted to integers. The operation is so frequently used in browsers so arm [added](https://community.arm.com/developer/ip-products/processors/b/processors-ip-blog/posts/armv8-a-architecture-2016-additions) a special instruction for it: FJCVTZS, which decyphers as "Floating-point Javascript Convert to Signed fixed-point, rounding toward Zero". This is an interesting example of software-hardware feedback loop in action.

But unless you use floating-point arithmetic to emulate integer arithmetic with lower range like JavaScript does, you are going to face occasional rounding errors. There are two natural ways to measure them:

* If you are working on hardware or spec-compliant exact software, you are concerned with *units in the last place* (ulps), which is the distance between two numbers in terms of how many representable numbers can fit between the real value and the result.
* If you are working on numerical algorithms, you care about relative precision, which is the absolute value of the approximation error divided by the real answer: $|\frac{v-v'}{v}|$.

In either case, what you usually do is you bound the errors. For exampole, if you perform a single basic arithmetic operation then the worst thing that can happen is the result rounding to the nearest representable number, implying that the error does not exceed 0.5 ulps. To convert this to relative error, it is useful to define a number called *machine epsilon* which equals to the difference between $1$ and the next representable value (that is, 2 to the negative power of however many bits are dedicated to mantissa). If we get result $x$ after a single arithmetic operation, this means that the real value lies in the $[x \cdot (1-\epsilon), x \cdot (1 + \epsilon)]$ range.

This is important to remember when making discrete "yes or no" decisions based on floating-point calculations. For example, to do comparisons you usually pick an epsilon depending on your application and proceed like this:

```c++
const float eps = std::numeric_limits<float>::epsilon; // ~2^(-23)
bool eq(float a, float b) {
    return abs(a - b) < eps;
}
```

While most operations with real numbers are commutative and assotiative, their rounding errors are not. You can tell compiler to ignore it with `-ffast-math`.

Note that, even though algebraically some operations are associative and commutative, enabling a large number of compiler optimizations, the their errors are not. Compilers are not allowed to produce incorrect results. You can disable this behavior with `-ffast-math`, although in many cases they will still need some help rearranging the expressions. Being aware of floating-point errors is especially important, because compilers don't always do a good job at estimating the errors.

### Interval Arithmetic

When analyzing numerical algorithms, it is useful to adopt the same method that is used in physics. Instead of working with values, we will work with intervals where the real value may be in.

Numerical stability is a notion in numerical analysis. An algorithm is called 'numerically stable' if an error, whatever its cause, does not grow to be much larger during the calculation

This happens if the problem is 'well-conditioned', meaning that the solution changes by only a small amount if the problem data are changed by a small amount.

A chain of arithmetic operations performed on some value are usually not a problem. Say, you are multiplying by various values. After the first multiplication, the relative error is bounded by machine epsilon. After the $n$ multiplications, the error is bound by $(1 + \epsilon)^n = 1 + n \epsilon + o(\epsilon^2)$. Same goes for the lower bound. You usually want to avoid long chains of operations over the same value because these errors add up.

So executing long chains of operations is not really a problem, but some other issues are. They are usually related to subtraction of numbers that are different in magnitude and relying on the difference to be exact. The general idea is to keep big numbers with big numbers and low numbers with low numbers.

As an example, consider function $f(x, y) = x^2 - y^2$. If $x$ and $y$ are close in magnitude, and if computed directly, the substraction will magnify errors of the squaring. The relative error can be $\epsilon \cdot |x|$, assuming $x$ is larger than $y$. Instead one can use the following formula: $(x + y) \cdot (x - y)$. The error will be bound by $\epsilon |x - y|$ and also be faster because it needs 2 additions and 1 multiplication while the original formula worked otherwise.

Next, consider the summation algorithm:

```c++
float s = 0;
for (int i = 0; i < n; i++)
    s += a[i];
```

The error is bound by $\epsilon \cdot n$, because we do $n$ summations. It can be large if $n$ is large. If the first value is $2^{23}$ and the other are ones, you are going to get $2^23$ as the result.

The obvious solution is to switch to a larger type such as `double`, but this isn't really a scalable method. A more general solution is Kahan summation. The idea is to store the parts that weren't added in a separate variable, which is then added to the next variable:

```c++
float s = 0, c = 0;
for (int i = 0; i < n; i++) {
    float y = a[i] - c; // c is zero on the first iteration
    float t = s + y;    // s may be big and y may be small, losing low-order bits of y
    c = (t - s) - y;    // (t - s) cancels high-order part of y
    s = t;
}
```

The relative error is bounded by $2 \epsilon + O(n \epsilon^2)$. The first term goes from the last summation, and the last term is due to the fact that we work with less-than-epsilon errors on each step.

### Double-double arithmetic

A more practical approach is to switch to a more precise data type, like `double`, 

Hardware has limits. One common software technique is to just bundle together two `double` variable: one for storing the value, and another for its errors, so that they actually represent $a+b$.

Similarly, you can define quad-double and higher precision arithmetic.

## Conversion to Decimal

It is unfortunate that humans evolved to have 10 fingers, because owing to this fact we ended up with a very clumsy numer system.

Digit is actually also a anatomical term meaning eiter a finger or a toe

Six fingers on each hand would be more convenient, because it would be straightforward to divide numbers by 2, 3, 4 and 6. This numbering system was used by ancient Babylonians, and it is still the reason why we have 60 seconds in a minute, 24 hours in a day, 12 months and 6 cans of beer in a pack: you can perfectly divide items by low divisors.

Four fingers on each hand (like in The Simpsons) would give us a very convenient octal system where you can divide by powers of 2, although most people would not start appreciating it untill invention of computers.

But here we are, and we have a problem of converting binary floating-point numbers to decimal numbers in scientific notation. But what does that even mean, exactly?

Note that some decimal numbers are not representable in finite form in binary. Here is a famous JavaScript joke (that you can reproduce by pressing F12 in your browser):

```
> 0.1
< 0.1
> 0.2
< 0.2
> 0.1+0.2
< 0.30000000000000004
```

Neither of them are exact, so JavaScript prints the shortest number that would be parsed back as the same number (reading numbers is defined similarly: it rounds to the closest representable number). The result of "0.3" and "0.1+0.2" is off by exactly one ULP, so it isn't printed as 0.3.

The way to approach any hard problem is to figure out how to solve some partial cases in then to figure out how to reduce the initial problem. Let's start with processing the sign bit: it's simple, just print "-" in front of a number in case it is 1. Next, we can check for special values.

Then, we can notice that some numbers are easy to print. If we have 23-bit mantissa and our exponent value is exactly 23, then we can reinterpret the mantissa as integer, add it to $2^23$ (the implicit 1) and then print it as we would print an integer. We can also do the same thing for small exponents, except that we would need to multiply that intermediate integer by a small power of two.

But what to do in general case, if the exponent value is either too large or too small? We can reduce the problem to the previous case by multiplying it by $\frac{10^a}{2^b}$ for some integers $a$ and $b$ with precise enough arithmetic so that the exponent is small.

Multiplying or dividing by 10 is the same as incrementing the exponent (the resulting one after the "e" in scientific notation, not the binary). The idea is to find a proper power of 10 so that the resulting number will have . We need to precalculate numbers of the form $\frac{10^a}{2^b}$ (since exponent is limited, there won't be many of them). To get the precalculated number, we need to look at the exponent (or possibly its neighbours).

The tricky part is the "shortest possible". It can be solved by printing digits one by one and trying to parse it back, but this would be too slow.

How many decimal digits do we need to print a `float`?

## Further Reading

"[What Every Computer Scientist Should Know About Floating-Point Arithmetic](https://www.itu.dk/~sestoft/bachelor/IEEE754_article.pdf)" by David Goldberg (1991).

[Grisu3](https://www.cs.tufts.edu/~nr/cs257/archive/florian-loitsch/printf.pdf)
