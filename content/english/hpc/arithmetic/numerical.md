---
title: Numerical Methods
weight: 2
---

Reaching the maximum possible precision is very rarely required from a practical algorithm. In real-world data, modeling and measurement errors are usually a few orders of magnitude larger than the errors that come from rounding floating-point numbers and such, so we are often perfectly happy with picking an approximate method that trades off precision for speed.

In this section, we will go through some classic numerical methods, just to get the gist of it.

## Newton's Method

Newton's method is a simple yet very powerful algorithm for finding approximate roots of real-valued functions, that is, the solutions to the following generic equation:

$$
f(x) = 0
$$

The only thing assumed about the function $f$ is that at least a one root exists and that $f(x)$ is continuous and differentiable on the search interval.

The main idea of the algorithm is to start with some initial approximation $x_0$ and then iteratively improve it by drawing the tangent to the graph of the function at $x = x_i$ and setting the next approximation $x_{i+1}$ equal to the $x$-coordinate of its intersection with the $x$-axis. The intuition is that if the function $f$ is "[good](https://en.wikipedia.org/wiki/Smoothness)", and $x_i$ is already close enough to the root, then $x_{i+1}$ will be even closer.

![](../img/newton.png)

To obtain the point of intersection for $x_n$, we need to equal its tangent line function to zero:

$$
0 = f(x_i) + (x_{i+1} - x_i) f'(x_i)
$$

from which we derive

$$
x_{i+1} = x_i - \frac{f(x_i)}{f'(x_i)}
$$

Newton's method is very important: it is the basis of most optimization solvers in science and engineering. 

### Square Root

As a simple example, let's derive the algorithm for the problem of finding square roots:

$$
x = \sqrt n \iff x^2 = n \iff f(x) = x^2 - n = 0
$$

If we substitute $f(x) = x^2 - n$ into the generic formula above, we can obtain the following update rule:

$$
x_{i+1} = x_i - \frac{x_i^2 - n}{2 x_i} = \frac{x_i + n / x_i}{2}
$$

In practice we also want to stop it as soon as it is close enough to the right answer, which we can simply check after each iteration:

```cpp
const double EPS = 1e-9;

double sqrt(double n) {
    double x = 1;
    while (abs(x * x - n) > eps)
        x = (x + n / x) / 2;
    return x;
}
```

The algorithm converges for many functions, although it does so reliably and provably only for a certain subset of them (e. g. convex functions). Another question is how fast the convergence is, if it occurs.

### Rate of Convergence

Let's run a few iterations of Newton's method to find the square root of $2$, starting with $x_0 = 1$, and check how many digits it got correct after each iteration:

<pre>
<b>1</b>
<b>1</b>.5
<b>1.41</b>66666666666666666666666666666666666666666666666666666666675
<b>1.41421</b>56862745098039215686274509803921568627450980392156862745
<b>1.41421356237</b>46899106262955788901349101165596221157440445849057
<b>1.41421356237309504880168</b>96235025302436149819257761974284982890
<b>1.41421356237309504880168872420969807856967187537</b>72340015610125
<b>1.4142135623730950488016887242096980785696718753769480731766796</b>
</pre>

Looking carefully, we can see that the number of accurate digits approximately doubles on each iteration. This fantastic convergence rate is not a coincidence.

To analyze convergence rate quantitatively, we need to consider a small relative error $\delta_i$ on the $i$-th iteration and determine how much smaller the error $\delta_{i+1}$ is on the next iteration:

$$
|\delta_i| = \frac{|x_n - x|}{x}
$$

We can express $x_i$ as $x \cdot (1 + \delta_i)$. Plugging it into the Newton iteration formula and dividing both sides by $x$ we get

$$
1 + \delta_{i+1} = \frac{1}{2} (1 + \delta_i + \frac{1}{1 + \delta_i}) = \frac{1}{2} (1 + \delta_i + 1 - \delta_i + \delta_i^2 + o(\delta_i^2)) = 1 + \frac{\delta_i^2}{2} + o(\delta_i^2)
$$

Here we have Taylor-expanded $(1 + \delta_i)^{-1}$ at $0$, using the assumption that the error $d_i$ is small (since the sequence converges, $d_i \ll 1$ for sufficiently large $n$).

Rearranging for $\delta_{i+1}$, we obtain

$$
\delta_{i+1} = \frac{\delta_i^2}{2} + o(\delta_i^2)
$$

which means that the error roughly squares (and halves) on each iteration once we are close to the solution. Since the logarithm $(- \log_{10} \delta_i)$ is roughly the number of accurate significant digits in the answer $x_i$, squaring the relative error corresponds precisely to doubling the number of significant
digits that we had observed.

This is known as *quadratic convergence*, and in fact this is not limited to finding square roots. With detailed proof being left as an exercise to the reader, it can be shown that, in general

$$
|\delta_{i+1}| = \frac{|f''(x_i)|}{2 \cdot |f'(x_n)|} \cdot \delta_i^2
$$

which results in at least quadratic convergence under a few additional assumptions, namely $f'(x)$ not being equal to $0$ and $f''(x)$ being continuous.

## Fast Inverse Square Root

The inverse square root of a floating-point number $\frac{1}{\sqrt x}$ is used in calculating normalized vectors, which are in turn extensively used in various simulation scenarios such as computer graphics, e. g. to determine angles of incidence and reflection to simulate lighting.

$$
\hat{v} = \frac{\vec v}{\sqrt {v_x^2 + v_y^2 + v_z^2}}
$$

Calculating inverse square root directly — by first calculating square root and then dividing by it — is extremely slow, because both of these operations are slow even though they are implemented in hardware.

But there is a surprisingly good approximation algorithm that takes advantage of the way floating-point numbers are stored in memory. In fact, it is so good that it has been [implemented in hardware](https://www.felixcloutier.com/x86/rsqrtps), so the algorithm is no longer relevant by itself for software engineers, but we are nonetheless going to walk through it for its intrinsic beauty and great educational value.

Apart from the method itself, quite interesting is the history of its creation. It is attributed to a game studio *id Software* that used it in their iconic 1999 game *Quake III Arena*, although apparently it got there by a chain of "I learned it from a guy who learned it from a guy" that seems to end on William Kahan (the same one that is responsible for IEEE 754 and Kahan summation algorithm).

It became popular in game developing community around 2005, when they released the source code of the game. Here is [the relevant excerpt from it](https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/q_math.c#L552), including the comments:

```c++
float Q_rsqrt(float number) {
    long i;
    float x2, y;
    const float threehalfs = 1.5F;

    x2 = number * 0.5F;
    y  = number;
    i  = * ( long * ) &y;                       // evil floating point bit level hacking
    i  = 0x5f3759df - ( i >> 1 );               // what the fuck? 
    y  = * ( float * ) &i;
    y  = y * ( threehalfs - ( x2 * y * y ) );   // 1st iteration
//  y  = y * ( threehalfs - ( x2 * y * y ) );   // 2nd iteration, this can be removed

    return y;
}
```

We will go through what it does step by step, but first we need to take a small detour.

### Calculating Approximate Logarithm

Before computers (or at least affordable calculators) became an everyday thing, people computed multiplication and related operations using logarithm tables — by looking up the logarithms of $a$ and $b$, adding them, and then finding the inverse logarithm of the result.

$$
a \times b = 10^{\log a + \log b} = \log^{-1}(\log a + \log b)
$$

You can do the same trick when computing $\frac{1}{\sqrt x}$ using the identity:

$$
\log \frac{1}{\sqrt x} = - \frac{1}{2} \log x
$$

The fast inverse square root is based on this identity, and so it needs to calculate the logarithm of $x$ very quickly. Turns out, it can be approximated by just reinterpreting a 32-bit `float` as integer.

[Recall](../float), floating-point numbers sequentially store the sign bit (equal to zero for positive values, which is our case), exponent $e_x$ and mantissa $m_x$, which corresponds to

$$
x = 2^{e_x} \cdot (1 + m_x)
$$

Its logarithm is therefore

$$
\log_2 x = e_x + \log_2 (1 + m_x)
$$

Since $m_x \in [0, 1)$, the logarithm on the right hand side can be approximated by

$$
\log_2 (1 + m_x) \approx m_x
$$

The approximation is exact at both ends of the intervals, but to account for average case we need to shift it by a small constant $\sigma$, therefore

$$
\log_2 x = e_x + \log_2 (1 + m_x) \approx e_x + m_x + \sigma
$$

Now, having this approximation in mind and defining $L=23$ as the number of mantissa bits in a `float` and $B=127$ for the exponent bias, when we reinterpret the bit-pattern of $x$ as an integer $I_x$, we get

$$
\begin{aligned}
I_x &= L(e_x + B + m_x)
\\  &= L(e_x + m_x + \sigma +B-\sigma )
\\  &\approx L\log_2 (x) + L (B-\sigma )
\end{aligned}
$$

When you tune $\sigma$ to minimize them mean square error, this results in a surprisingly accurate approximation.

![](../img/approx.svg)

Now, expressing the logarithm from the approximation, we get

$$
\log_2 x \approx \frac{I_x}{L} - (B - \sigma)
$$

Cool. Now, where were we? Oh, yes, we wanted to calculate the inverse square root.

### Approximating Result

To calculate $y = \frac{1}{\sqrt x}$ using the identity $\log_2 y = - \frac{1}{2} \log_2 x$, we can plug it into our approximation formula and get

$$
\frac{I_y}{L} - (B - \sigma)
\approx
- \frac{1}{2} ( \frac{I_x}{L} - (B - \sigma) )
$$

Solving for $I_y$:

$$
I_y \approx \frac{3}{2} L (B - \sigma) - \frac{1}{2} I_x
$$

It turns out, we don't even need to calculate logarithm in the first place: the formula above is just a constant minus the half of integer reinterpretation of $x$. It is written in the code as:

```cpp
i = * ( long * ) &y;
i = 0x5f3759df - ( i >> 1 );
```

We reinterpret `y` as an integer on the first line, and then plug into in to the formula, the first term of which is the magic number $\frac{3}{2} L (B - \sigma) = \mathtt{0x5F3759DF}$, while the second is calculated with a binary shift instead of division.

### Iterating with Newton's Method

What we have next is a couple hand-coded iterations of Newton's method with $f(y) = \frac{1}{y^2} - x$ and a very good initial value. It's update rule is

$$
f'(y) = - \frac{2}{y^3} \implies y_{i+1} = y_{i} (\frac{3}{2} - \frac{x}{2} y_i^2) = \frac{y_i (3 - x y_i^2)}{2}
$$

which is written in code as

```cpp
x2 = number * 0.5F;
y  = y * ( threehalfs - ( x2 * y * y ) );
```

The initial approximation is so good that just one iteration was enough for game development purposes. It falls within 99.8% of the correct answer after just the first iteration, and can be reiterated further to improve accuracy — which is what is done in the hardware: the x86 does a few of them and guarantees a relative error of no more than $1.5 \times 2^{-12}$.

## Further Reading

[Wikipedia article of fast inverse square root](https://en.wikipedia.org/wiki/Fast_inverse_square_root#Floating-point_representation)

[Introduction to numerical methods at MIT](https://ocw.mit.edu/courses/mathematics/18-330-introduction-to-numerical-analysis-spring-2012/lecture-notes/MIT18_330S12_Chapter4.pdf)
