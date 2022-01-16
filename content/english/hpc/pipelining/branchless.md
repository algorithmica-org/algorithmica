---
title: Branchless Programming
weight: 3
---

Sometimes, the best way 

We are going to continue [the case study of branching](../branching)

We can remove explicit branching completely by using a special `cmov` ("conditional move") instruction that assigns a value based on a condition.

```c++
for (int i = 0; i < N; i++)
    s += (a[i] < 50 : a[i] : 0);
```

This is roughly equivalent to this algebraic trick:

```c++
s += (a[i] < 50) * a[i];
```

```nasm
mov     ecx, -4000000
; todo

mov     esi, dword ptr [rdx + a + 4000000]
cmp     esi, 50
cmovge  esi, eax
add     dword ptr [rsp + 12], esi
add     rdx, 4
jne     .LBB0_4
```
---

The codes seem equivalent. My guess is that the compiler doesn't know that `s + a[i]` does not cause integer overflow.

(The compiler can't optimize it because it's technically [not allowed to](/hpc/compilation/contracts): despite `y - x` being valid, `x - y` could over/underflow, causing undefined behavior. Although fully correct, I guess the compiler just doesn't date executing it.)

Branchless computing tricks like this one are especially important in all sorts of parallel algorithms.

The `cmov` variant doesn't care about probabilities of branches. It only wins if the branch probability if 75% chance, which usually is the heuristic threshold set in compilers.

This is a legal optimization, but I guess an implicit contract has evolved between application programmers and compiler engineers that if you write a ternary operator, then you kind of telling that it is likely going to be an unpredictable branch.

Such techniques are called *branchless* or *branch-free* programming. It is very beneficial for SIMD.

When you get rid of `volatile`, compiler gets permission to vectorize the loop. It looks remarkably similar, but using vector instructions instead of the scalar ones:

```c++
/* volatile */ int s = 0;

for (int i = 0; i < N; i++)
    if (a[i] < 50)
        s += a[i];
```

~0.3 per element, which is mainly bottlenecked by [the memory](/hpc/cpu-cache/bandwidth).

### Forcing Predication

There are ways how to tell the compiler that `cmov` is beneficial You can use `__builtin_expect_with_probability(cond, true, 0.5` in GCC and `__builtin_unpredictable(cond)` in Clang, but both these hints are lost by the time optimizer decides what is more beneficial: branch or a cmov.

https://bugs.llvm.org/show_bug.cgi?id=40027

Branching is expensive.

You can use `cmov` instructions. And something more complex in simd.

Unfortunately.

Some more complex examples.

Branchless and sometimes branch-free.

Predication

Hardware (stats-based) branch predictor is built-in in CPUs,
$\implies$ Replacing high-entropy `if`'s with predictable ones help
You can replace conditional assignments with arithmetic:
  `x = cond * a + (1 - cond) * b`
This became a common pattern, so CPU manufacturers added `CMOV` op
  that does `x = (cond ? a : b)` in one cycle
*^This masking trick will be used a lot for SIMD and CUDA later*

### Real-World Examples

**Strings.** Oversimplifying things, the struct of an `std::string` is composed of a pointer to a null-terminated char array (aka c-string) allocated somewhere on the heap and the string size.

A very common value for strings is the empty string (which is also its default value), which you also need to handle somehow. An idiomatic thing to do is to put `nullptr` as pointer and 0 as the string length, and then check if the pointer is null or if the size is zero.

However, this check requires a separate branch and divergence in the execution path. So what we can do instead is to allocate a zero string somewhere (a pointer to a zero byte) and then simply point all empty strings there. All string operations have to read this useless zero byte, but it is still cheaper than doing the branch check.

**Binary search.** Binary search [can be implemented](/hpc/algorithms/binary-search) without branches, and on small (fitting into cache) arrays it works ~4x faster than the branchy `std::lower_bound`.

That there are no substantial reasons why compilers can't do this on their own, but unfortunately this is just how it is right now.

