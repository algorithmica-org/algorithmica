---
title: Precomputation
weight: 8
---

When compilers can infer that a certain variable does not depend on any user-provided data, they can compute its value during compile time and turn it into a constant by embedding it into the generated machine code.

This optimization helps performance a lot, but it is not a part of the C++ standard, so compilers don't *have to* do that. When a compile-time computation is either hard to implement or time-intensive, a compiler may pass on that opportunity.

### Constant Expressions

For a more reliable solution, in modern C++ you can mark a function as `constexpr`; if it is called by passing constants its value is guaranteed to be computed during compile time:

```c++
constexpr int fibonacci(int n) {
    if (n <= 2)
        return 1;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

static_assert(fibonacci(10) == 55);
```

These functions have some restrictions like that they only call other `constexpr` functions and can't do memory allocation, but otherwise, they are executed "as is."

Note that while `constexpr` functions don't cost anything during run time, they still increase compilation time, so at least remotely care about their efficiency and don't put something NP-complete in them:

```c++
constexpr int fibonacci(int n) {
    int a = 1, b = 1;
    while (n--) {
        int c = a + b;
        a = b;
        b = c;
    }
    return b;
}
```

There used to be many more limitations in earlier C++ standards, like you could not use any sort of state inside them and had to rely on recursion, so the whole process felt more like Haskell programming rather than C++. Since C++17, you can even compute static arrays using the imperative style, which is useful for precomputing lookup tables:

```c++
struct Precalc {
    int isqrt[1000];

    constexpr Precalc() : isqrt{} {
        for (int i = 0; i < 1000; i++)
            isqrt[i] = int(sqrt(i));
    }
};

constexpr Precalc P;

static_assert(P.isqrt[42] == 6);
```

Note that when you call `constexpr` functions while passing non-constants, the compiler may or may not compute them during compile time:

```c++
for (int i = 0; i < 100; i++)
    cout << fibonacci(i) << endl;
```

In this example, even though technically we perform a constant number of iterations and call `fibonacci` with parameters known at compile time, they are technically not compile-time constants. It's up to the compiler whether to optimize this loop or not — and for heavy computations, it often chooses not to.

<!--

### Code Generation

There are plenty of languages that support computing *data* during compile time, but none can produce efficient code at all times.

One huge example is generating lexers and parsers: which is usually done in.

For example, CUDA and OpenCL are mostly C, and have no support for metaprogramming.

At some point (and perhaps to this day), these languages had no way to unroll loops, so people would write a [jinja template](https://jinja.palletsprojects.com/en/3.0.x/), call the thing from Python, and then compile.

It is not uncommon to use a templating engine to generate code. For example, CUDA (a GPU programming language) has no loop unrolling

-->
