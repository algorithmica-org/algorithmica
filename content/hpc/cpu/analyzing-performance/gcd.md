---
title: Binary GCD
weight: 4
---

The main purpose of this book is not to learn computer architecture for the sake of learning it, but to acquire real-world skills in software optimization.

For this aid, it is filled with — and, in fact, mostly comprised of — examples of problems that are harder to optimize than summing two arrays together. This one is the first of many.

This section describes a variant of `gcd` that is 2x faster than what the standard library has to offer.

## Euclid's Algorithm

Euclid's algorithm solves the problem of finding the greatest common divisor (GCD) of two integer numbers $a$ and $b$, which is, as the name suggests, the largest such number $g$ that divides both $a$ and $b$:

$$
\gcd(a, b) = \max_{g: \\; g|a \\, \land \\, g | b} g
$$

You probably know it from a CS textbook already, but let me briefly remind it anyway. It is based on the following formula, assuming that $a > b$:

$$
\gcd(a, b) = \begin{cases}
    a, & b = 0
\\\ \gcd(b, a \mod b), & b > 0
\end{cases}
$$

This is true, because if $g = \gcd(a, b)$ divides both $a$ and $b$, it should also divide $(a \mod b = a - k \cdot b)$, but any larger divisor $d$ of $b$ will not: $d > g$ implies that $d$ couldn't divide $a$ and thus won't divide $(a - k \cdot b)$.

This formula is the algorithm itself: you can simply apply it recursively, and it will eventually converge to the $b = 0$ case.

The textbook also probably mentioned that the worst possible input to Euclid's algorithm that maximizes the number of steps are consecutive Fibonacci numbers, and since they grow exponentially, the running time of the algorithm is worst-case logarithmic. This is also true for the *average* time, if we define it as the expected time on uniformly distributed integers. [The wikipedia article](https://en.wikipedia.org/wiki/Euclidean_algorithm) has a cryptic derivation of a more precise $0.84 \cdot \ln n$ estimate.

![You can see bright blue lines at the proportions of the golden ratio](../img/euclid.svg)

There are many ways you can implement Euclid's algorithm. The simplest would be just to convert the definition into code:

```c++
int gcd(int a, int b) {
    if (b == 0)
        return a;
    else
        return gcd(b, a % b);
}
```

You can rewrite it more compactly like this:

```c++
int gcd(int a, int b) {
    return (b ? gcd(b, a % b) : a);
}
```

You can rewrite it as a loop, which is more close to how it will be executed on the hardware. It won't be faster though, because compilers can easily optimize tail recurion.

```c++
int gcd(int a, int b) {
    while (b > 0) {
        a %= b;
        std::swap(a, b);
    }
    return a;
}
```

You can even write rewrite the body of the loop as this confusing one-liner — and it will even compile without undefined behavior warnings since C++17.

```c++
int gcd(int a, int b) {
    while (b) b ^= a ^= b ^= a %= b;
    return a;
}
```

All of these, as well as `std::gcd`, which was introduced in C++17 but has been available in GCC since a long time ago as `__gcd`, are almost equivalent and get compiled into functionally the following assembly loop:

```asm
# a = %eax, b = %edx
LOOP:
    # modulo in assembly (will be explained later):
    movl  %edx, %r8d
    cltd
    idivl %r8d
    movl  %r8d, %eax
    # (a and b are already swapped now)
    # if b is not zero, jump to beginning:
    testl %edx, %edx
    jg    LOOP
    # if b is zero, move result to eax??? and return:
    movl  %r8d, %eax
    ret
```

If you run `perf` on it, you'll see that it spends 90% of time on the `idivl` line. What's happening here?

## How Division Works in x86

In short: very poorly.

Integer division is notoriously hard to implement in hardware. The circuitry takes a lot of space in the ALU, the computation has a lot of stages, and as a result `div` and its siblings routinely take 15-20 cycles to complete. Since nobody wanted to duplicate all this mess for a separate modulo operation, `div` serves both purposes.

To make a 64-bit division, you need to put dividend in `eax` register — very specifically — and call `div` with the divisor as its sole operand. After this, the quotient will be in `eax` and the remainer will be in `edx`.

The procedure for other sizes is the same, except that the division works faster for smaller data types.

There is one kind of division though that works very well in hardware: division by a power of 2.

## Binary GCD

The *binary GCD algorithm* was discovered around the same time as Euclid's, but on the other end of the civilized world — in ancient China. In 1967, it was rediscovered by Josef Stein for use in computers that either don't have division instruction or have a very slow one: it wasn't uncommon for CPUs of that era to use hundreds or thousands of cycles for rare or complex operations.

Analagous to the Euclidean algorithm, it is based on a few similar observations:

1. $\gcd(0, b) = b$ and, symmetrically, $\gcd(a, 0) = a$
2. $\gcd(2a, 2b) = 2 \cdot \gcd(a, b)$
3. $\gcd(2a, b) = \gcd(a, b)$ if $b$ is odd and, symmetrically, $\gcd(a, b) = \gcd(a, 2b)$ if $a$ is odd
4. $\gcd(a, b) = \gcd(|a − b|, \min(a, b))$, if $a$ and $b$ are both odd

Similarly, the algorithm itself is just repeated application of these identities.

The running time is still logarithmic, which is even easier to show because after each of these identities one of the arguments will be divided by 2 (except for the last case, in which the new first argument, an absolute difference of two odd numbers, will be divided in the next iteration). What makes it interesting is that the only arithmetic operations it uses are binary shifts, comparisons and substraction, all of which typically take one cycle.

The reason this algorithm is not in the textbooks is because it can't be implemented as a simple one-liner anymore:

```c++
// todo: test it
int gcd(int a, int b) {
    // base cases (1)
    if (a == 0) return b;
    if (b == 0) return a;
    if (a == b) return a;

    if (a % 2 == 0) {
        if (b % 2 == 0) // a is even, b is even (2)
            return 2 * gcd(a / 2, b / 2);
        else            // a is even, b is odd (3)
            return gcd(a / 2, b);
    } else {
        if (b % 2 == 0) // a is odd, b is even (3)
            return gcd(a, b / 2);
        else            // a is odd, b is odd (4)
            return gcd(abs(a - b), min(a, b));
    }
}
```

Let's run it, and... it sucks. The difference in speed is indeed 2x, but on the other side of equation. This is mainly because of all the branching needed to distinguish between cases. Let's start optimizing.

The first optimization: let's replace divisions by 2 with divisions by whatever high power of 2 we can. We can easily do it with `__builtin_ctz`, the "count trailing zeros" instruction available on modern CPUs. Whenever we are supposed to divide by 2, we call this function instead, which will give us the exact amount to right-shift a number by. If the numbers are random, this is expected to decrease number of iterations by almost a factor 2, because $1 + \frac{1}{2} + \frac{1}{4} + \frac{1}{8} + \ldots \to 2$.

After we've done that, we can notice that condition 2 can only be true once, in the beginning, because every other identity will leave one of the numbers odd. Therefore we can only do it once in the beginning and not check for this case during the loop.

Next, we can notice that after we entered condition 4 and applied its identity, $a$ always be even and $b$ will always be odd, so we instantly know that we are going to be in condition 3 on the next iteration. This means that we can actually de-evenize $a$ right away, but if we do so each time we hit condition 4, this will mean that we can only ever be either in condition 4 or terminating by condition 1.

Combining these ideas, we get the following implementation:

```c++
int gcd(int a, int b) {
    if (a == 0) return b;
    if (b == 0) return a;

    int az = __builtin_ctz(a);
    int bz = __builtin_ctz(b);
    int shift = min(az, bz);
    a >>= az;
    
    while (b != 0) {
        b >>= bz;
        int dba = b - a;
        int dab = a - b;
        bz = __builtin_ctz(dba);
        a = min(a, b);
        b = max(dba, dab);
    }
    
    return a << shift;
}
```

Almost twice as fast. Can we break the 100ns barrier?

This is the time to stare at assembly again.

After implementing these ideas and twiddling around and randomly rearranging instructions and re-running benchmarks a few times, we arrive at a final version:

```c++
int gcd(int a, int b) {
    if (!a || !b) return a | b;

    char az = __builtin_ctz(a);
    char bz = __builtin_ctz(b);
    char shift = min(az, bz);
    a >>= az;
    
    while (true) {
        b >>= bz;
        int dba = b - a;
        int dab = a - b;
        bz = __builtin_ctz(dba);
        if (dba == 0) break;
        a = min(a, b);
        b = max(dba, dab);
    }
    
    return a << shift;
}
```

98ns. Good enough.

If somebody wants to try to shove off a few more nanoseconds by re-writing assembly by hand of trying a lookup table to save a few last iterations, please let me know.
