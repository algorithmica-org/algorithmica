---
title: Contract Programming
weight: 4
---

In safe languages like Java and Rust, you normally have a well-defined behavior for every possible operation and every possible input. There are some things that are *underdefined*, like the order of keys in a hash table, but these are usually some minor details left to implementation for potential performance gains in the future.

In contrast, C and C++ take the concept of undefined behavior to another level. Certain operations don't cause an error during compilation or runtime but are just not *allowed* — in the sense of there being a contract between a programmer and a compiler, that in case of undefined behavior the compiler can do literally anything, including formatting your hard drive.

But compiler authors are not interested in formatting your hard drive of blowing up your monitor. Instead, undefined behavior is used to guarantee a lack of corner cases and help optimization.

For example, consider the case of signed overflow. On almost all architectures, signed integers overflow the same way as unsigned ones, with `INT_MAX + 1 == INT_MIN`, but yet this behavior is not a part of the C/C++ standard. This was very much intentional: if you disallow signed integer overflow, then `(x + 1) > x` is guaranteed to be always true for `int`, but not for `unsigned int`. For signed types, this allows compilers to optimize such checks away.

As a more naturally occurring example, consider the case of a loop with an integer control variable. C++ and Rust are advocating for using an unsigned integer (`size_t` / `usize`), while C programmers stubbornly keep using `int`. For a reason why, consider the following `for` loop:

```cpp
for (unsigned int i = 0; i < n; i++) {
    // ...
}
```

How many times does this loop execute? There are technically two valid answers: $n$ and infinity, the second being the case if $n$ exceeds $2^{32}$ so that $i$ keeps resetting to zero every $2^{32}$ iterations. While the former is probably the one assumed by the programmer, to comply with the language spec, compiler still has to insert additional runtime checks and consider the two cases, which should be optimized differently. On the other hand, the `int` version would make exactly $n$ iterations, because the possibility of a signed overflow is defined out of existence.

### Removing Corner Cases

Safe programming style usually involves making a lot of runtime checks, but these do not have to come at the cost of performance. For example, Rust famously uses array bounds checks when indexing. In C++ STL, `vector` and `array` also have an "unsafe" `[]` operator and a "safe" `.at()` method that goes something like this:

```cpp
T at(size_t k) {
    if (k >= size())
        throw std::out_of_range("Array index exceeds its size");
    return _memory[k];
}
```

An interesting fact is that these checks are quite rarely actually executed during runtime, because compiler can often prove during compilation time that everything is fine — for example, when iterating in a `for` loop from 1 to the array size and indexing $i$-th element on each step.

When compiler can't prove inexistence of corner cases, but you can, you can use the mechanism of undefined behavior to provide it with additional information. Clang has a helpful `__builtin_assume` function where you can put a statement that is guaranteed to be true, and compiler will use this assumption. In GCC you can do the same with `__builtin_unreachable`:

```cpp
void assume(bool pred) {
    if (!pred)
        __builtin_unreachable();
}
```

Then you can put `assume(k < vector.size())` before `at` and the bounds check should be optimized away.

### Arithmetic

Corner cases and tiny details are also something you should keep in mind when doing arithmetic. 

One example we've already mentioned before is the fact that floating-point arithmetic is not technically commutative, even though nobody cares about results being correct to the last bit. Compiler needs to comply with the C language spec regarding the order of operations, which blocks some potential optimizations. Strict compliance can be disabled with the `-ffast-math` flag, which is also included in `-Ofast`.

In integer arithmetic, corner cases are also often hurting performance. Consider the case of division by 2:

```cpp
unsigned div_unsigned(unsigned x) {
    return x / 2;
}
```

It is widely known to be optimizable with a single bit shift (`x >> 1`):

```nasm
shr eax
```

This is definitely correct for all *positive* numbers. What about the general case?

```cpp
int div_signed(int x) {
    return x / 2;
}
```

If `x` is negative, then just shifting doesn't work, at least because the upper bit will be zero, indicating a positive result. We need to insert some crutches that will become more clear when we get to the chapter about integer arithmetic:

```nasm
mov ebx, eax
shr ebx, 31
add ebx, eax
sar ebx
```

But the positive case is clearly what was intended. Here we can also use UB to exclude that corner case:

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

Since each iteration of this loop is independent, it can be executed in parallel and vectorized. But is it, technically?

If arrays `a` and `b` intersect, there may be a problem. Consider the case when `b == a + 1`, that is, if `b` is a just a memory view of `a` starting with the second element. In this case, the next iteration depends on the previous one, and the only correct solution is execute the loop sequentially.

This is why we have `const` and `restrict` keywords. The first one enforces that that we won't modify memory with the pointer variable, and the second is a way to tell compiler that the memory is guaranteed to be not aliased.

```cpp
void add(int * __restrict__ a, const int * __restrict__ b, int n) {
    for (int i = 0; i < n; i++)
        a[i] += b[i];
}
```

These keywords are also a good idea to use by themselves for the purpose of self-documenting.
