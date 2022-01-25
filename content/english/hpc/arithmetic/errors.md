---
title: Rounding Errors
weight: 2
---

The way rounding works in hardware floats is remarkably simple: it occurs if and only if the result of the operation is not representable exactly, and by default gets rounded to the nearest representable number (and to the nearest zero-ending number in case of a tie).

Apart from the default mode (also known as Banker's rounding), you can [set](https://www.cplusplus.com/reference/cfenv/fesetround/) other rounding logic with 4 more modes:

* round to nearest, with perfect ties always rounding "away" from zero;
* round up (toward $+∞$; negative results thus round toward zero);
* round down (toward $-∞$; negative results thus round away from zero);
* round toward zero (a truncation of the binary result).

The alternative rounding modes are also useful in diagnosing numerical instability. If the results of a subroutine vary substantially between rounding to the positive and negative infinities, then it indicates susceptibility to round-off errors. Is a better test than switching all computations to a lower precision and checking whether the result changed by too much because the default rounding to nearest results in the right "expected" value given enough averaging: statistically, half of the time they are rounding up and the other are rounding down, so they cancel each other.

Note that while most operations with real numbers are commutative and associative, their rounding errors are not: even the result of $(x+y+z)$ depends on the order of summation. Compilers are not allowed to produce non-spec-compliant results, so this disables some potential optimizations that involve rearranging operands. You can disable this strict compliance with the `-ffast-math` flag in GCC and Clang, although you need to be aware that this lets compilers sometimes choose less precise computation paths.

It seems surprising to expect this guarantee from hardware that performs complex calculations such as natural logarithms and square roots, but this is it: you are guaranteed to get the highest precision possible from all operations. This makes it remarkably easy to analyze round-off errors, as we will see in a bit.

## Measuring and Mitigating Errors

There are two natural ways to measure computational errors:

* The engineers who create hardware or spec-compliant exact software are concerned with *units in the last place* (ulps), which is the distance between two numbers in terms of how many representable numbers can fit between the precise real value and the actual result of the computation.
* People that are working on numerical algorithms care about *relative precision*, which is the absolute value of the approximation error divided by the real answer: $|\frac{v-v'}{v}|$.

In either case, the usual tactic to analyze errors is to assume the worst case and simply bound them.

If you perform a single basic arithmetic operation, then the worst thing that can happen is the result rounding to the nearest representable number, meaning that the error does not exceed 0.5 ulps. To reason about relative errors the same way, we can define a number $\epsilon$ called *machine epsilon*, equal to the difference between $1$ and the next representable value (which should be equal to 2 to the negative power of however many bits are dedicated to mantissa).

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

After the first multiplication, the value of $x$ relative to the value of the real product is bounded by $(1 + \epsilon)$, and after each additional multiplication, this upper bound is multiplied by another $(1 + \epsilon)$. By induction, after $n$ multiplications, the computed value is bound by $(1 + \epsilon)^n = 1 + n \epsilon + O(\epsilon^2)$ and a similar lower bound.

This implies that the relative error is $O(n \epsilon)$, which is sort of okay, because usually $n \ll \frac{1}{\epsilon}$.

For example of a numerically *unstable* computation, consider the function

$$
f(x, y) = x^2 - y^2
$$

Assuming $x > y$, the maximum value this function can return is roughly

$$
x^2 \cdot (1 + \epsilon) - y^2 \cdot (1 - \epsilon)
$$

corresponding to the absolute error of

$$
x^2 \cdot (1 + \epsilon) - y^2 \cdot (1 - \epsilon) - (x^2 - y^2) = (x^2 + y^2) \cdot \epsilon
$$

and hence the relative error of

$$
\frac{x^2 + y^2}{x^2 - y^2} \cdot \epsilon
$$

If $x$ and $y$ are close in magnitude, the error will be $O(\epsilon \cdot |x|)$.

Under direct computation, the subtraction "magnifies" the errors of squaring. But this can be fixed by instead using the following formula:

$$
f(x, y) = x^2 - y^2 = (x + y) \cdot (x - y)
$$

In this one, it is easy to show that the error is be bound by $\epsilon \cdot |x - y|$. It is also faster because it needs 2 additions and 1 multiplication: one fast addition more and one slow multiplication less compared to the original.

### Kahan Summation

From the previous example, we can see that long chains of operations are not a problem, but adding and subtracting numbers of different magnitude is. The general approach to dealing with such problems is to try to keep big numbers with big numbers and low numbers with low numbers.

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

Of course, a more general approach would be to switch to a more precise data type, like `double`, either way effectively squaring the machine epsilon. It can sort of be scaled by bundling two `double` variables together: one for storing the value, and another for its non-representable errors, so that they actually represent $a+b$. This approach is known as *double-double* arithmetic, and it can be similarly generalized to define quad-double and higher precision arithmetic.

<!--

## Conversion to Decimal

It is unfortunate that humans evolved to have 10 fingers, because owing to this fact we ended up with a very clumsy number system.

Digit is actually also a anatomical term meaning either a finger or a toe

Six fingers on each hand would be more convenient, because it would be straightforward to divide numbers by 2, 3, 4 and 6. This numbering system was used by ancient Babylonians, and it is still the reason why we have 60 seconds in a minute, 24 hours in a day, 12 months and 6 cans of beer in a pack: you can perfectly divide items by low divisors.

Four fingers on each hand (like in The Simpsons) would give us a very convenient octal system where you can divide by powers of 2, although most people would not start appreciating it until invention of computers.

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

Multiplying or dividing by 10 is the same as incrementing the exponent (the resulting one after the "e" in scientific notation, not the binary). The idea is to find a proper power of 10 so that the resulting number will have . We need to precalculate numbers of the form $\frac{10^a}{2^b}$ (since exponent is limited, there won't be many of them). To get the precalculated number, we need to look at the exponent (or possibly its neighbors).

The tricky part is the "shortest possible". It can be solved by printing digits one by one and trying to parse it back, but this would be too slow.

How many decimal digits do we need to print a `float`?

-->

