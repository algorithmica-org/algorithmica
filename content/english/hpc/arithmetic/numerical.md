---
title: Numerical Methods
weight: 2
---

You do not always want to go for maximum possible precision. In real-world data, modeling and measurement errors are usually a few orders of magnitude larger than the errors that come from rounding floating-point numbers, so often we are fine with picking an approximate method that trades off precision for speed.

In this section, we will go through some classic numerical methods.

## Newton's Method

Newton's method, also known as the Newton–Raphson method, is a simple yet very powerfull algorithm for finding approximate roots of real-valued functions, that is, the solutions to the following general equation:

$$
f(x) = 0
$$

The only thing assumed about the function $f$ is that at least a one root exists and that $f(x)$ is continuous and differentiable on the search interval.

The main idea is to start with some initial approximation $x_0$ and then iteratively improve it by drawing the tangent to the graph of the function at $x = x_i$ and setting the next approximation $x_{i+1}$ equal to the $x$-coordinate of its intersection with the $x$-axis. The intuition is that if the function $f$ is "[good](https://en.wikipedia.org/wiki/Smoothness)", and $x_i$ is close enough to the root, then $x_{i+1}$ will be even closer.

![](../img/newton.png)

To obtain the point of intersection for $x_n$, we need to equal its tangent line function to zero:

$$
0 = f(x_i) + (x_{i+1} - x_i) f'(x_i)
$$

from which we derive:

$$
x_{i+1} = x_i - \frac{f(x_i)}{f'(x_i)}
$$

Newton's method is very important: it is the basis of most optimization solvers in science and engineering. As a simple example, let's derive the algorithm for the problem of finding square roots:

$$
x = \sqrt n \iff x^2 = n \iff f(x) = x^2 - n = 0
$$

If we substitute $f(x) = x^2 - n$, we obtain the following update rule:

$$
x_{i+1} = x_i - \frac{x_i^2 - n}{2 x_i} = \frac{x_i + n / x_i}{2}
$$

The algorithm converges for many functions, although it does so reliably and provably only for a certain subset of them (e. g. convex functions). Another question is how fast the convergence is, if it occurs.

Let's run the Newton's method to find the square root of $2$, starting with $x_0 = 1$, and look how many digits it got correct after each iteration:

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

We can express $x_i$ as $x \cdot (1 + \delta_i)$, and plugging it into the Newton iteration formula and dividing both sides by $x$ we get:

$$
1 + \delta_{i+1} = \frac{1}{2} (1 + \delta_i + \frac{1}{1 + \delta_i}) = \frac{1}{2} (1 + \delta_i + 1 - \delta_i + \delta_i^2 + o(\delta_i^2)) = 1 + \frac{\delta_i^2}{2} + o(\delta_i^2)
$$

Here we have Taylor-expanded $(1 + \delta_i)^{-1}$ at $0$, using the assumption that the error $d_i$ is small (since the sequence converges, $d_i \ll 1$ for sufficiently large $n$). After final rearrangement, we obtain:

$$
\delta_{i+1} = \frac{\delta_i^2}{2} + o(\delta_i^2)
$$

which means the error roughly squares (and halves) on each iteration once we are close to the
solution. Since the logarithm $(- \log_{10} \delta_i)$ is roughly the number of accurate significant digits in the answer $x_i$, squaring the relative error corresponds precisely to doubling the number of significant
digits that we observed.

This is known as quadratic convergence, and in fact this is not limited to finding square roots only. With detailed proof being left as an exercise to the reader, it can be shown that, in general:

$$
|\delta_{i+1}| = \frac{|f''(x_i)|}{2 \cdot |f'(x_n)|} \cdot \delta_i^2
$$

which results in at least quadratic convergence under a few additional assumptions, namely $f'(x)$ not being equal to $0$ and $f''(x)$ being continuous.

## Logistic Regression

In machine learning, perhaps the most popular way of doing black-box classification is logistic regression.

Say, we want to classify $28 \times 28$ black-and-white pictures of digits into one of 10 categories (0..9):

![Numbers that some Canadian students wrote on test blanks make MNIST dataset](../img/mnist.png)

Computationally, it works like this. If we are working with $n$-dimensional data, which we need to classify into one of $m$ classes, then we multiply the input vector by a parameter matrix of size $n \times m$, and then apply a special "softmax" function to the output $m$-element vector:

$$
softmax(x)\_k = \frac{e^{x_k}}{\sum_i^m e_{x_i}}
$$

In other words, what this function does is it calculates elementwise exponent of its input vector and then normalized it so that the elements add up to 1. Since the output has $m$ positive elements that add up to 1, it can be treated as a probability distribution that the sample belongs to a certain class. We can then look at the highest probability prediction and take it as the answer of the model.

We look at a large dataset of samples and fit our parameter matrix so that we get the most answers correct. We will not go into detail about how to fit it, but once we did, we need to *inference* it, that is, to feed it new data and get predictions.

This is pretty much all that a performance engineer needs to know about machine learning. For now, we are only concerned with the computational side of things.

```c++
float w[10][28*28];
// 796 x 10
int predict(float a) {
    float s[10] = {0};

    for (int k = 0; k < 10; k++)
        for (int i = 0; i < 28*28; i++)
            s[k] += a[i] * w[k][i];

    // there is not problem with calculating exponent of small numbers,
    // but exponent of large numbers may overflow
    int mx = *std::max_element(s, s + 10);
    float sumexp = 0;
    for (int i = 0; i < 10; i++) {
        s[i] = exp(s[i] - mx);
        sumexp += s[i];
    }

    int argmax = 0;
    
    for (int i = 0; i < 10; i++) {
        s[i] /= sumexp;
        if (s[i] > s[argmax])
            argmax = i;
    }

    return argmax;
}
```

This isn't exactly worth optimizing, because that's just ~10k operations anyway, but our use case could be bigger. For example, neural networks are not fundamentally different: they just use longer chains of transformations, and not just matrix multiplication followed by a softmax.

This can also be used in a hot spot. For example, computer chess programs use similar models to determine the value of a position (the probability of winning). By the way, this is how "1-3-3-5-9" heuristic approach: you can train a logistic regression on a large dataset of chess positions that are turned into piece count differences, and that's what weights are going to look like. Score in other games works in a similar way.

The first thing we can notice is that we don't actually need to implement softmax, because we can notice that the largest logit (this is how pre-softmax numbers are called) will be largest after the softmax, so we only need to take argmax after the matrix multiplication.

Nobody in their sane mind uses C++ for training ML models.

### Quantization

Machine learning is one of the cases where we need neither range nor precision. The whole point of machine learning is to learn functions that are robust to small perturbations in data. The input data is noisy, so why our computations shouldn't be? Plus, errors should cancel each other. We can also force the matrix parameters to be in a certain range.

Using lower precision has two advantages:

1. It takes less time to fetch data.
2. We can use SIMD instructions that packs more values together.

```c++
char w[10][28*28];

int predict(char a) {
    short max = 0, argmax = 0;

    for (int k = 0; k < 10; k++) {
        short s = 0;
        for (int i = 0; i < 28*28; i++)
            s += a[i] * w[k][i];
        if (s > max)
            s = 0, argmax = k;
    }

    return argmax;
}
```

## Fast Inverse Square Root

The inverse square root of a floating point number $\frac{1}{\sqrt x}$ is used in calculating normalized vectors, which are extensively used in various simulation scenarious such as computer graphics, e. g. to determine angles of incidence and reflection to simulate lighting:

$$
\hat{v} = \frac{\vec v}{\sqrt {v_x^2 + v_y^2 + v_z^2}}
$$

Calculating inverse square root directly — by first calculating square root and then dividing by it — is extremely slow, because both of these operations are slow even when implemented in hardware. But, quite remarkably, you can create a very good approximation of inverse square root operation. The following numerical algorithm is not as generic as the previous ones, but it is a very useful for educational and historical reasons. With subsequent hardware advancements, especially the x86 SSE instruction `rsqrtss` that does exactly this, this method is not generally applicable to modern computing, though it remains an interesting example both historically and educationally.

It is important from educational and historical perspective. The algorithm is beautiful.

![](../img/norm.svg)

Apart from the method itself, quite interesting are the history of its creation. It was developed by a game studio *id Software* for a 1999 game Quake III Arena, for which they released the source code in 2005. Although it got there by a chain of "I learned it from a guy who learned it from a guy" that seems to end on William Kahan.

But anyway, it was popularized by Quake in game development community. Here is the original C code from [released source](https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/q_math.c#L552), including the original comment text:

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

### Calculating Approximate Logarithm

Before computers (or at least affordable calculators) became an everyday thing, people computed multiplication and related complex operations by a table of logarithms: you can look up logarithms of $a$ and $b$, add them, and then find the inverse logarithm of the result. You can do the same trick when computing $\frac{1}{\sqrt x}$ using the identity:

$$
\log \frac{1}{\sqrt x} = - \frac{1}{2} \log x
$$

The fast inverse square root is based on this identity, and so it needs to calculate the logarithm of $x$ very quickly, which it turns out to be easily approximated by just reinterpreting a 32-bit `float` as integer. Recall, floating-point numbers sequentially store sign bit ($0$ for positive values, which is our case), the exponent $e_x$ and mantissa $m_x$, which corresponds to:

$$
x = 2^{e_x} (1 + m_x)
$$

If we reinterpret it as an integer:

$$
\log_2 x = e_x + \log_2 (1 + m_x) \approx e_x + m_x
$$

and since $m \in [0, 1)$, the logarithm on the right hand side can be approximated by

$$
\log_2 (1 + m_x) = m_x + \sigma
$$

The approximation is exact at both ends of the intervals, but to account for average case we need to shift it by a small constant $\sigma$. This results in a surprisingly good approximation.

![](../img/approx.svg)

$$
\log_2 x \approx \frac{I_x}{L} - (B - \sigma)
$$

### Approximating Result

Remembering that we need to calculate $y = \frac{1}{\sqrt x}$ and the identity $\log_2 y = - \frac{1}{2} \log_2 x$, we can plug it into our approximation formula and get:

$$
\frac{I_y}{L} - (B - \sigma)
\approx
- \frac{1}{2} ( \frac{I_x}{L} - (B - \sigma) )
$$

Solving for $I_y$:

$$
I_y \approx \frac{3}{2} L (B - \sigma) - \frac{1}{2} I_x
$$

which is written in the code as:

```c++
i  = 0x5f3759df - ( i >> 1 );
```

The first term here is the magic number $\frac{3}{2} L (B - \sigma) = \mathtt{0x5F3759DF}$, while the second is calculated with a binary shift instead of division.

### Iterating with Newton's Method

Next, we have a few hand-coded iterations of Newton's method with $f(y) = \frac{1}{y^2} - x$ and a very good initial value:

$$
f'(y) = - \frac{2}{y^3} \implies y_{i+1} = y_{i} (\frac{3}{2} - \frac{x}{2} y_i^2) = \frac{y_i (3 - x y_i^2)}{2}
$$

which is written as:

```c++
x2 = number * 0.5F;
y  = y * ( threehalfs - ( x2 * y * y ) );
```

In fact, so the initial approximation is so good that just one iteration was enough for game development purposes, falling within 99.8% after just the first iteration, and can be reiterated further to improve accuracy (which is used in modern hardware; SIMD instruction guarantees error of no more than $1.5 \times 2^{-12}$ and computes all that in just 4 cycles and throughput of 1).

## Further Reading

[Wikipedia article of fast inverse square root](https://en.wikipedia.org/wiki/Fast_inverse_square_root#Floating-point_representation)

[Introduction to numerical methods at MIT](https://ocw.mit.edu/courses/mathematics/18-330-introduction-to-numerical-analysis-spring-2012/lecture-notes/MIT18_330S12_Chapter4.pdf)
