---
title: Floating-Point Arithmetic
weight: 1
---

The users of floating-point arithmetic deserve one of these IQ bell curve memes — because this is how the relationship between it and most people typically proceeds:

- Beginner programmers use it everywhere as if it was some magic unlimited-precision data type.
- Then they discover that `0.1 + 0.2 != 0.3` or some other quirk like that, freak out, start thinking that some random error term is added to every computation, and for many years aviod any real data types completely.
- Then they finally man up, read the specification of how IEEE-754 floats work and start using them appropriately.

Most people are unfortunately still at stage 2, breeding various misconceptions about floating-point arithmetic — thinking that it is fundamentally imprecise and unstable, and slower than integer arithmetic.

![](../img/iq.svg)

But these are all just myths. Floating-point arithmetic is often *faster* than integer arithmetic because of specialized instructions, and real number representations are thoroughly standartized and follow simple and deterministic rules in terms of rounding, allowing you to manage computational errors reliably.

In fact, it is so reliable that some high-level programming languages, most notably JavaScript, don't have integers at all. In JavaScript, there is only one `number` type, which is internally stored as a 64-bit `double`, and due to the way floating-point arithmetic works, all integer numbers between $-2^{53}$ and $2^{53}$ and results of computations involving them can be stored exactly, so from a programmer's perspective, there is little practical need for a separate integer type.

One notable exception is when you need to perform bitwise operations with numbers, which *floating-point units* (the coprocessors responsible for operations on floating-point numbers) typically don't support. In this case, they need to be converted to integers, which is so frequently used in JavaScript-enabled browsers that arm [added a special "FJCVTZS" instruction](https://community.arm.com/developer/ip-products/processors/b/processors-ip-blog/posts/armv8-a-architecture-2016-additions) that stands for "Floating-point Javascript Convert to Signed fixed-point, rounding toward Zero" and does what it says it does — converts real to integer the exact same way as JavaScript — which is an interesting example of the software-hardware feedback loop in action.

But unless you are a JavaScript developer who uses real types exclusively to emulate integer arithmetic, you probably need a more in-depth guide about floating-point arithmetic, so we are going to start with a broader subject.

## Real Number Representations

If you need to deal with real (non-integer) numbers, you have several options with varying applicability. Before jumping straight to floating-point numbers, which is what most of this article is about, we want to discuss the available alternatives and the motivation behind them — after all, people who avoid floating-point arithmetic do have a point.

### Symbolic Expressions

The first and the most cumbersome approach is to store not the resulting values themselves but the algebraic expressions that produce them.

Here is a simple example. In some applications, such as computational geometry, apart from addding, subtracting and multiplying numbers, you also need to divide without rounding, producing a rational number, which can be exactly represented with a ratio of two integers:

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

This way we can represent numbers in the form $\pm \\; m \times 2^e$ where both $m$ and $e$ are bounded *and possibly negative* integers — which would correspond to negative or small numbers respectively. The distribution of these numbers is very much non-uniform: there are as many numbers in the $[0, 1]$ range as in the $[0, +\infty)$ range.

Note that these representations are not unique for some numbers. For example, number $1$ can be represented as

$$
1 \times 2^0 = 2 \times 2^{-1} = 256 \times 2^{-8}
$$

and in 28 other ways that don't overflow the mantissa.

This can be problematic for some applications, such as comparisons or hashing. To fix this, we can *normalize* these representations using a certain convention. In decimal, the [standard form](https://en.wikipedia.org/wiki/Scientific_notation) is to always put the comma after the first digit (`6.022e23`), and for binary we can do the same:

$$
42 = 10101_2 = 1.0101_2 \times 2^5
$$

Notice that, following this rule, the first bit is always 1. It is redundant to store it explicitly, so we will just pretend that it's there and only store the other bits, which correspond to some rational number in the $[0, 1)$ range. The set of representable numbers is now roughly

$$
\{ \pm \; (1 + m) \cdot 2^e \; | \; m = \frac{x}{2^{32}}, \; x \in [0, 2^{32}) \}
$$

Since $m$ is now a nonnegative value, we will now make it unsigned integer, and instead add a separate boolean field for the sign of the number:

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

Many applications that require higher levels of precision use software floating-point arithmetic in a similar fashion. Buf of course, you don't want to execute a sequence 10 or so instructions that this code compiles to each time you want to multiply two real numbers, so floating-point arithmetic is implemented in hardware — often in separate coprocessors due to its complexity.

The FPU of x86 (often referred to as x87) has separate registers and its own tiny instruction set that supports memory operations, basic arithmetic, trigonometry and some common operations such logarithm, exponent and square root.

## IEEE 754 Floats

When we designed our DIY floating-point type, we omitted quite a lot of important little details:

- How many bits do we dedicate for the mantissa and the exponent?
- Does a "0" sign bit means "+" or is it the other way around?
- How are these bits stored in memory?
- How do we represent 0?
- How exactly does rounding happen?
- What happens if we divide by zero?
- What happens if we take a square root of a negative number?
- What happens if increment the largest representable number?
- Can we somehow detect if one of the above three happened?

Most of the early computers didn't have floating-point arithmetic, and when vendors started adding floating-point coprocessors, they had slightly different vision for what answers to those questions should be. Diverse implementations made it difficult to use floating-point arithmetic reliably and portably — particularily for people developing compilers.

In 1985, the Institute of Electrical and Electronics Engineers published a standard (called [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754)) that provided a formal specification of how floating-point numbers should work, which was quickly adopted by the vendors and is now used in virtually all general-purpose computers.

### Float Formats

Similar to our handmade float implementation, hardware floats use one bit for sign and a variable number of bits for exponent and mantissa. For example, the standard 32-bit `float` encoding uses the first (highest) bit for sign, the next 8 bits for exponent, and the 23 remaining bits for mantissa. 

![](../img/float.svg)

One of the reasons why they are stored in this exact order is so that it would be easier to compare and sort them: if you flip the sign bit, you can simply use the same comparator circuit as for unsigned integers.

IEEE 754 and a few consequent standards define not one, but *several* representations that differ in sizes, most notably:

|      Type | Sign | Exponent | Mantissa | Total bits | Approx. decimal digits |
|----------:|------|----------|----------|------------|------------------------|
|    single | 1    | 8        | 23       | 32         | ~7.2                   |
|    double | 1    | 11       | 52       | 64         | ~15.9                  |
|      half | 1    | 5        | 10       | 16         | ~3.3                   |
|  extended | 1    | 15       | 64       | 80         | ~19.2                  |
| quadruple | 1    | 15       | 112      | 128        | ~34.0                  |
|  bfloat16 | 1    | 8        | 7        | 16         | ~2.3                   |

Their availability ranges from chip to chip:

- Most CPUs support single- and double-precision — which is what `float` and `double` types refer to in C.
- Extended formats are exclusive to x86, and are available in C as the `long double` type, which falls back to double precision on arm. The choice of 64 bits for mantissa is so that every `long long` integer can be represented exactly. There is also a 40-bit format that similarly allocates 32 mantissa bits.
- Quaruple as well as the 256-bit "octuple" formats are only used for specific scientific computations and are not supported by general-purpose hardware.
- Half-precision arithmetic only supports a small subset of operations, and is generally used for machine learning applications, especially neural networks, because they tend to do a large amount of calculation, but don't require a high level of precision.
- Half-precision is being gradually replaced by bfloat, which trades off 3 mantissa bits to have the same range as single-precision, enabling interoperability with it. It is mostly being adopted by specialized hardware: TPUs, FGPAs and GPUs. The name stands for "[Brain](https://en.wikipedia.org/wiki/Google_Brain) float".

Lower precision types need less memory bandwidth to move them around and usually take less cycles to operate on (e. g. the division instruction may take $x$, $y$, or $z$ cycles depending on the type), which is why they are preferred when error tolerance allows it.

Deep learning, emerging as a very popular and computationally-intensive field, created a huge demand for low-precision matrix multiplication, which led to manufacturers developing separate hardware or at least adding specialized instructions that support these types of computations — most notably, Google developing a custom chip called TPU (*tensor processing unit*) that specializes on multiplying 128-by-128 bfloat matrices, and NVIDIA adding "tensor cores", capable of performing 4-by-4 matrix multiplication in one go, to all their newer GPUs.

Apart from their sizes, most of behavior is exactly the same between all floating-point types, which we will now clarify.

## Handling Corner Cases

The default way integer arithmetic deals with corner cases such as division by zero is to crash.

Sometimes a software carsh in turn causes a real, physical one. In 1996, the maiden flight of the [Ariane 5](https://en.wikipedia.org/wiki/Ariane_5) (the space launch vehicle that ESA uses to lift stuff into low Earth orbit) ended in [a catastrophic explosion](https://www.youtube.com/watch?v=gp_D8r-2hwk) due to the policty of aborting computation on arithmetic error, which in this case was a floating-point to integer conversion overflow, that led to the navigation system thinking that it was off course and making a large correction, eventually causing the disintegration of a $1B rocket.

There is a way to gracefully handle corner cases such like these: hardware interrupts. When an exception occurs, CPU:

- interrupts the execution of a program;
- packs every all relevant information into a data structure called "interrupt vector";
- passes it to the operating system, which in turn either calls the handling code if it exists (the "try-except" block) or terminates the program otherwise.

This is a complex mechanism that deserves an article of its own, but since this is a book about performance, the only thing you need to know is that they are quite slow and not desirable in a real-time systems such as navigating rockets.

### NaNs and Infinities

Floating-point arithmetic often deals with noisy, real-world data, and exceptions there are much more common than in the integer case. For this reason, the default behavior is different. Instead of crashing, the result is substituted with a special value without interrupting the executing, unless the programmer explicitly wants to.

The first type of such values are the two infinities: a positive and a negative one. They are generated if the result of an operation can't fit within in the representable range, and they are treated as such in arithmetic.

$$
\begin{aligned}
   -∞ < x &< ∞
\\  ∞ + x &= ∞
\\  x ÷ ∞ &= 0
\end{aligned}
$$

What happens if we, say, divide a value by zero? Should it be a negative or a positive infinity? This case in actually unambigious because, somewhat less intuitively, there are also two zeros: a positive and a negative one.

$$
    \frac{1}{+0} = +∞
\;\;\;\;  \frac{1}{-0} = -∞
$$

Zeros are encoded by setting all bits to zero, except for the sign bit in the negative case. Infinities are encoded by setting all their exponent bits to one and all mantissa bits to zero, but the sign bit distinguishing between a positive and a negative infinity.

The other type is the "not-a-mumber” (NaN), which is generated as the result of mathematically incorrect operations:

$$
\log(-1),\; \arccos(1.01),\; ∞ − ∞,\; −∞ + ∞,\; 0 × ∞,\; 0 ÷ 0,\; ∞ ÷ ∞
$$

There are two types of NaNs: a signalling NaN and a quiet NaN. A signalling NaN raises an exception flag, which may or may not cause an immediate hardware interrupt becased on FPU configuration, while a quiet NaN just propagates through almost every arithmetic operation, resulting in more NaNs.

Both NaNs are encoded as all their exponent set to ones and the mantissa part being everything other than all zeroes (to distinguish them from infinities).

### Rounding

The way rounding works in hardware floats is remarkably simple: it occurs if and only if the result of the operation is not representable exactly, and by default gets rounded to the nearest representable number (and to the nearest zero-ending number in case of a tie).

Apart from the default mode (also known as Banker's rounding), you can [set](https://www.cplusplus.com/reference/cfenv/fesetround/) other rounding logic with 4 more modes:

* round to nearest, with ties always rounding "away" from zero;
* round up (toward $+∞$; negative results thus round toward zero);
* round down (toward $-∞$; negative results thus round away from zero);
* round toward zero (truncation of the binary result).

The alternative rounding modes are also useful in diagnosing numerical instability. If the results of a subroutine vary substantially between rounding to the positive and negative infinities, then it indicates susceptibility to round-off errors. Is a better test than switching all computations to a lower precision and checking whether the result changed by too much, because the default rounding to nearest results in the right "expected" value given enough averaging: statistically, half of the time they are rounding up and the other are rounding down, so they cancel each other.

Note that while most operations with real numbers are commutative and assotiative, their rounding errors are not: even the result of $(x+y+z)$ depends on the order of summation. Compilers are not allowed to produce non-spec-compliant results, so this disables some potential optimizations that involve rearranging operands. You can disable this strict compliance with the `-ffast-math` flag in GCC and Clang, although you need to be aware that this lets compilers sometimes choose less precise computation paths.

It seems surprising to expect this guarantee from hardware that performs complex calculations such as natural logarithms and square roots, but this is it: you guaranteed to get the highest precision possible from all operations. This makes it remarkably easy to analyze round-off errors, as we will see in a bit.

## Measuring and Mitigating Errors

There are two natural ways to measure computational errors:

* The engineers who create hardware or spec-compliant exact software are concerned with *units in the last place* (ulps), which is the distance between two numbers in terms of how many representable numbers can fit between the precise real value and the actual result of computation.
* People that are working on numerical algorithms care about *relative precision*, which is the absolute value of the approximation error divided by the real answer: $|\frac{v-v'}{v}|$.

In either case, the usual tactic to analyze errors is to assume the worst case and simply bound them.

If you perform a single basic arithmetic operation, then the worst thing that can happen is the result rounding to the nearest representable number, meaning that the error in this case does not exceed 0.5 ulps. To reason about relative errors the same way, we can define a number $\epsilon$ called *machine epsilon*, equal to the difference between $1$ and the next representable value (which should be equal to 2 to the negative power of however many bits are dedicated to mantissa).

This means that if after a single arithmetic operation you get result $x$, then the real value is somewhere in the range

$$
[x \cdot (1-\epsilon),\; x \cdot (1 + \epsilon)]
$$

The omnipresence of errors is especially important to remember when making discrete "yes or no" decisions based on the results of floating-point calculations. For example, here is how you should check for equality:

```c++
const float eps = std::numeric_limits<float>::epsilon; // ~2^(-23)
bool eq(float a, float b) {
    return abs(a - b) <= eps;
}
```

The value of epsilon should depend on the application: the one above — the machine epsilon for `float` — is only good for no more than one floating-point operation.

### Interval Arithmetic

An algorithm is called *numerically stable* if its error, whatever its cause, does not grow to be much larger during the calculation. This happens if the problem is *well-conditioned*, meaning that the solution changes by only a small amount if the problem data are changed by a small amount.

When analyzing numerical algorithms, it is often useful to adopt the same method that is used in experimental physics: instead of working with unknown real values, we will work with the intervals where they may be in.

For example, consider a chain of operations where we consecutively multiply a variable by arbitrary real numbers:

```cpp
float x = 1;
for (int i = 0; i < n; i++)
    x *= a[i];
```

After the first multiplication, the value of $x$ relative to the value of the real product is bounded by $(1 + \epsilon)$, and after each additional multiplication this upper bound is multiplied by another $(1 + \epsilon)$. By induction, after $n$ multiplications, the computed value is bound by $(1 + \epsilon)^n = 1 + n \epsilon + O(\epsilon^2)$ and a similar lower bound.

This implies that the relative error is $O(n \epsilon)$, which is sort of okay, because usually $n \ll \frac{1}{\epsilon}$.

For example of a numerically *unstable* computation, consider the function

$$
f(x, y) = x^2 - y^2
$$

Assuming $x > y$, the maximum value this function can return is roughly

$$
x^2 \cdot (1 + \epsilon) - y^2 \cdot (1 - \epsilon)
$$

corresponding to the absolute arror of

$$
x^2 \cdot (1 + \epsilon) - y^2 \cdot (1 - \epsilon) - (x^2 - y^2) = (x^2 + y^2) \cdot \epsilon
$$

and hence the relative error of

$$
\frac{x^2 + y^2}{x^2 - y^2} \cdot \epsilon
$$

If $x$ and $y$ are close in magnitude, the error will be $O(\epsilon \cdot |x|)$.

Under direct computation, the substraction "magnifies" the errors of the squaring. But this can be fixed by instead using the following formula:

$$
f(x, y) = x^2 - y^2 = (x + y) \cdot (x - y)
$$

In this one, it is easy to show that the error is be bound by $\epsilon \cdot |x - y|$. It is also faster because it needs 2 additions and 1 multiplication: one fast addition more and one slow multiplication less compared to the original.

### Kahan Summation

From previous example, we can see that long chains of operations are not a problem, but adding and substracting numbers of different magnitude is. The general approach to dealing with such problems is to try to keep big numbers with big numbers and low numbers with low numbers.

Consider the standard summation algorithm:

```c++
float s = 0;
for (int i = 0; i < n; i++)
    s += a[i];
```

Since we are performing summations and not multiplications, its relative error is no longer just bounded by $O(\epsilon \cdot n)$, but heavily depends on the input.

In the most ridiculous case, if the first value is $2^{23}$ and the others are ones, the sum is going to be $2^{23}$ regardless of $n$, which can be verified by executing the following code and observing that it simply prints $16777216 = 2^{23}$ twice:

```cpp
const int n = (1<<24);
printf("%d\n", n);

float s = n;
for (int i = 0; i < n; i++)
    s += 1.0;

printf("%f\n", s);
```

This happens because `float` has only 23 mantissa bits, and so $2^{23} + 1$ is the first integer number that can't be represented exactly and has to be rounded down, which happens every time we try to add $1$ to $s = 2^{23}$. The error is indeed $O(n \cdot \epsilon)$ but in terms of the absolute error, not the relative one: in the example above, it is $2$, and it would go up to infinity if the last number happened to be $-2^{23}$.

The obvious solution is to switch to a larger type such as `double`, but this isn't really a scalable method. An elegant solution is to store the parts that weren't added in a separate variable, which is then added to the next variable:

```c++
float s = 0, c = 0;
for (int i = 0; i < n; i++) {
    float y = a[i] - c; // c is zero on the first iteration
    float t = s + y;    // s may be big and y may be small, losing low-order bits of y
    c = (t - s) - y;    // (t - s) cancels high-order part of y
    s = t;
}
```

This trick is known as *Kahan summation*. Its relative error is bounded by $2 \epsilon + O(n \epsilon^2)$: the first term comes from the very last summation, and the second term is due to the fact that we work with less-than-epsilon errors on each step.

Of course, a more general approach would be to switch to a more precise data type, like `double`, either way effectively squaring the machine epsilon. It can sort of be scaled by budling two `double` variable together ne for storing the value, and another for its non-representable errors, so that they actually represent $a+b$. This approach is known as *double-double* arithmetic, and can be similarly generalized to define quad-double and higher precision arithmetic.

<!--

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

-->

## Further Reading

If you are so inclined, you can read the classic "[What Every Computer Scientist Should Know About Floating-Point Arithmetic](https://www.itu.dk/~sestoft/bachelor/IEEE754_article.pdf)" (1991) and [the paper introducing Grisu3](https://www.cs.tufts.edu/~nr/cs257/archive/florian-loitsch/printf.pdf), the current state-of-the art for printing floating-point numbers.
