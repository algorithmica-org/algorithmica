---
title: Contract Programming
weight: 6
---

In "safe" languages like Java and Rust, you normally have well-defined behavior for every possible operation and every possible input. There are some things that are *under-defined*, like the order of keys in a hash table, but these are usually some minor details left to implementation for potential performance gains in the future.

In contrast, C and C++ take the concept of undefined behavior to another level. Certain operations don't cause an error during compilation or runtime but are just not *allowed* — in the sense of there being a *contract* between the programmer and the compiler, that in case of undefined behavior the compiler can do literally anything, including formatting your hard drive.

But compiler engineers are not interested in formatting your hard drive of blowing up your monitor. Instead, undefined behavior is used to guarantee a lack of corner cases and help optimization.

### Why Undefined Behavior Exists

There are two major groups of actions that cause undefined behavior:

- Operations that are almost certainly unintentional bugs, like dividing by zero, dereferencing a null pointer, or reading from uninitialized memory. You want to catch these as soon as possible during testing, so crashing or having some non-deterministic behavior is better than having them always do a fixed fallback action such as returning zero.

  You can compile and run a program with *sanitizers* to catch undefined behavior early. In GCC and Clang, you can use the `-fsanitize=undefined` flag, and some operations that frequently cause UB will be instrumented to detect it at runtime.

- Operations that have slightly different observable behavior on different platforms: for example, the result of left-shifting an integer by more than 31 bits is undefined, because the relevant instructions are implemented differently on Arm and x86 CPUs. If you standardize one specific behavior, then all programs compiled for the other platform will have to spend a few more cycles checking for that edge case, so it is best to leave it either undefined.

  Sometimes, when there is a legitimate use case for some platform-specific behavior, it can be left *implementation-defined* instead of being undefined. For example, the result of right-shifting a [negative integer](/hpc/arithmetic/integer) depends on the platform: it either shifts in zeros or ones (e. g. right shifting `11010110 = -42` by one may mean either `01101011 = 107` or `11101011 = -21`, both use cases being realistic).

Designating something as undefined instead of implementation-defined behavior also helps compilers in optimization.

For example, consider the case of signed integer overflow. On almost all architectures, [signed integers](/hpc/arithmetic/integer) overflow the same way as unsigned ones, with `INT_MAX + 1 == INT_MIN`, but yet this is undefined behavior in the C/C++ standard. This is very much intentional: if you disallow signed integer overflow, then `(x + 1) > x` is guaranteed to be always true for `int`, but not for `unsigned int`, because `(x + 1)` may overflow. For signed types, this allows compilers to optimize such checks away.

As a more naturally occurring example, consider the case of a loop with an integer control variable. Modern C++ and languages like Rust are advocating for using an unsigned integer (`size_t` / `usize`), while C programmers stubbornly keep using `int`. To understand why, consider the following `for` loop:

```cpp
for (unsigned int i = 0; i < n; i++) {
    // ...
}
```

How many times does this loop execute? There are technically two valid answers: $n$ and infinity, the second being the case if $n$ exceeds $2^{32}$ so that $i$ keeps resetting to zero every $2^{32}$ iterations. While the former is probably the one assumed by the programmer, to comply with the language spec, the compiler still has to insert additional runtime checks and consider the two cases, which should be optimized differently. On the other hand, the `int` version would make exactly $n$ iterations, because the very possibility of a signed overflow is defined out of existence.

### Removing Corner Cases

"Safe" programming style usually involves making a lot of runtime checks, but these do not have to come at the cost of performance.

For example, Rust famously uses bounds checking when indexing arrays and other random access structures. In C++ STL, `vector` and `array` have an "unsafe" `[]` operator and a "safe" `.at()` method that goes something like this:

```cpp
T at(size_t k) {
    if (k >= size())
        throw std::out_of_range("Array index exceeds its size");
    return _memory[k];
}
```

Interestingly, these checks are rarely actually executed during runtime, because the compiler can often prove, during compilation time, that each access will be within bounds. For example, when iterating in a `for` loop from 1 to the array size and indexing $i$-th element on each step, nothing illegal can possibly happen, so the bounds checks can be safely optimized away.

### Assumptions

When the compiler can't prove the inexistence of corner cases, but you can, this additional information can be provided using the mechanism of undefined behavior.

Clang has a helpful `__builtin_assume` function where you can put a statement that is guaranteed to be true, and the compiler will use this assumption in optimization. In GCC you can do the same with `__builtin_unreachable`:

```cpp
void assume(bool pred) {
    if (!pred)
        __builtin_unreachable();
}
```

For instance, you can put `assume(k < vector.size())` before `at` in the example above, and the bounds check should be optimized away.

It is also quite useful to combine `assume` with `assert` and `static_assert` to find bugs: you can use the same function to check preconditions in the debug build, and then use them to improve performance in the production build.

<!--

```cpp
void assume(bool pred) {
    if (!pred)
        #ifdef
        __builtin_unreachable();
        #else
        exit(0); // ?
        #endif
}
```

-->

### Arithmetic

Corner cases are something you should keep in mind especially when optimizing arithmetic. 

For floating-point arithmetic, this is less of a concern because you can just disable strict standard compliance with the `-ffast-math` flag (which is also included in `-Ofast`): you almost have to do it anyway because otherwise the compiler can't do anything but execute arithmetic operations in the exact same order as in the code without any optimization, because even algebraically correct rearrangements result in slightly different rounding errors.

For integer arithmetic, this is different, because the results always have to be exact. Consider the case of division by 2:

```cpp
unsigned div_unsigned(unsigned x) {
    return x / 2;
}
```

A widely known optimization is to replace it with a single right shift (`x >> 1`):

```nasm
shr eax
```

This is certainly correct for all *positive* numbers. But what about the general case?

```cpp
int div_signed(int x) {
    return x / 2;
}
```

If `x` is negative, then just shifting doesn't work, regardless of whether shifting is done in zeros or sign bits:

- If we shift in zeros, we get a non-negative result.
- If we shift in sign bits, then rounding will happen towards negative infinity instead of zero (`-5 / 2` needs to be equal to `-2` instead of `-3`).

So, for the general case, we have to insert some crutches to make it work:

```nasm
mov ebx, eax
shr ebx, 31
add ebx, eax
sar ebx
```

But the positive case is clearly what was intended. Here we can also use the `assume` mechanism to exclude that corner case:

```cpp
int div_assume(int x) {
    assume(x >= 0);
    return x / 2;
}
```

Because of nuances like this, it is often beneficial to expand the algebra in intermediate functions and manually simplify arithmetic yourself rather than relying on the compiler to do it.

### Memory Aliasing

Compilers are quite bad at optimizing operations that involve memory reads and writes. This is because they often don't have enough context for the optimization to be correct.

Consider the following example:

```c++
void add(int *a, int *b, int n) {
    for (int i = 0; i < n; i++)
        a[i] += b[i];
}
```

Since each iteration of this loop is independent, it can be executed in parallel and [vectorized](/hpc/simd). But is it, technically?

There may be a problem if arrays `a` and `b` intersect. Consider the case when `b == a + 1`, that is, if `b` is a just a memory view of `a` starting with the second element. In this case, the next iteration depends on the previous one, and the only correct solution is execute the loop sequentially.

This is why we have `const` and `restrict` keywords. The first one enforces that that we won't modify memory with the pointer variable, and the second is a way to tell compiler that the memory is guaranteed to be not aliased.

```cpp
void add(int * __restrict__ a, const int * __restrict__ b, int n) {
    for (int i = 0; i < n; i++)
        a[i] += b[i];
}
```

These keywords are also a good idea to use by themselves for the purpose of self-documenting.

### C++20 Contracts

Contract programming is an underused, but very powerful technique.

Design-by-contract actually made it into the C++20 standard in the form [contract sattributes](http://www.hellenico.gr/cpp/w/cpp/language/attributes/contract.html), which are functionally equivalent to our hand-made, compiler-specific `assume`:

```c++
T at(size_t k) [[ expects: k < n ]] {
    return _memory[k];
}
```

There are 3 types of attributes — `expects`, `ensures`, and `assert` — respectively used for specifying pre- and post-conditions in functions and general assertions that can be anywhere in the program.

Unfortunately, this exciting new feature is not yet implemented in any major C++ compiler, but maybe around 2022-2023 you will be able to write code like this:

```c++
bool is_power_of_two(int m) {
    return m > 0 && (m & (m - 1) == 0);
}

int mod_power_of_two(int x, int m)
    [[ expects: x >= 0 ]]
    [[ expects: is_power_of_two(m) ]]
    [[ ensures r: r >= 0 && r < m ]]
{
    float r = x & (m - 1);
    [[ assert: r = x % m ]];
    return r;
}
```

Some forms of contract programming are also available in other performance-oriented languages such as [Rust](https://docs.rs/contracts/latest/contracts/) and [D](https://dlang.org/spec/contracts.html).

A general and language-agnostic advice is to always inspect the assembly that the compiler produced, and then, if it is not what you were hoping for, try to think about corner cases that may be limiting the compiler from optimizing it.
