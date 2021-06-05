---
title: Floating-Point Arithmetic
weight: 1
---

Programmers tend to avoid floating-point arithmetic. Common misconception is that some random noise is added to every number. It's not true. You can reliably manage errors, and often compute stuff precisely.

16-bit, 32-bit, 64-bit.

There are 3 parts. For example, for 32-bit `float`:

$+1.0123 \cdot 2^e$

The first one is implied.

- The first (highest) bit is reserved for sign. This leaves an awkward exception for 0 and -0.
- The next 8 bits represent exponent, which is, how 
- The next 23 bits represent *significant*, also called *mantissa*.

![](../img/float.svg)

There is a lot of awkwardness with floating-point numbers. They are also hard to parse from scientific notation.

Real numbers

sign, mantissa, exponent

bfloat, float, double

## IEEE 754 Formats

There are also 40- and 80-bit types.

Higher precision types need more memory bandwidth and usually take more cycles to finish (e. g. division takes x, y, and z cycles depending on type).

For some applications, it is so critical that manufacturers create a separate hardware or at least an instruction that supports these types.

For example, you don't need a lot of precision for machine learning (since input is noisy, why wouldn't computations be noisy too?), and most of it consists of matrix multiplications. Google has created a custom chip called TPU (tensor processing unit) that works with bfloat, and NVIDIA added "tensor cores" capable of doing 4x4 matrix multiplication in one go, but only for a specific data type.

### Exceptions in IEEE 754

Overflow, underflow, division by zero, invalit, inexact

### Other Floating-Point Types

### Rounding

In the IEEE standard, rounding occurs if (and *only* if) the result of the operation is not exact.

https://www.cplusplus.com/reference/cfenv/fesetround/

The ties banker's rounding. You can actually change the rounding behavior in case of a tie. The standard has 5 different modes:

* round to nearest, where ties round to the nearest even digit in the required position (default)
* round to nearest, where ties round away from zero
* round up (toward $+\infty$; negative results thus round toward zero)
* round down (toward $-\infty$; negative results thus round away from zero)
* round toward zero (truncation)

The alternative rounding modes are also useful in diagnosing numerical instability: if the results of a subroutine vary substantially between rounding to + and − infinity then it is likely numerically unstable and affected by round-off error.

When the real result is exactly between two representable numbers

You can also set rounding to be always towards

There are many issues with floating-point numbers.

In floating-point numbers, `-0` is not the same as `+0`.

You usually pick an epsilon and do comparisons like this:

```c++
const float eps = 1e-6;
bool eq(float a, float b) {
    return abs(a - b) < eps;
}
```

## Measuring and Mitigating Errors

*Relative* error and *absolute* error.


### Precise Calculation

In some cases, it is actually benefitial to convert from integers to floating point. For example, x86 has a separate instruction to calculate square root for floating-point types. You can calculate `sqrt` of an integer less than $2^{23}$ (or $2^53$ in case of `double`), floor it and expect it to be perfectly accurate.

> First rule of floating-point numbers: do not use floating-point numbers.

Computer algebra systems store and operate on symbolic values without evaluating them as real numbers.

In computer algebra systems, you resort to representing rational numbers with an actual ratio, like this:

```c++
struct r {
	int x, y;
	r(int x) : x(x), y(1) {}
	r(int x, int y) : x(x), y(y) {
		int g = gcd(x, y);
		x /= g;
		y /= g;
	}
};

r operator+(r a, r b) { return r{a.x * b.y + a.y * b.x, a.y * b.y}; }
r operator*(r a, r b) { return r{a.x * b.x, a.y * b.y}; }
r operator/(r a, r b) { return r{a.x * b.x, a.y * b.y}; }
bool operator<(r a, r b) { return a.x * b.y < b.x * a.y; }
// ...and so on, you get the idea
```

The way they are defined to behave is via rounding to the next, an to odd one in case of a tie.

While operations with real numbers are assotiative, their rounding errors are not. You can tell compiler to ignore it with `-ffast-math`.
