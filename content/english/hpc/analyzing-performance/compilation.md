---
title: Negotiating with Compilers
weight: 2
---

The main benefit of [learning assembly language](../assembly) is not the ability to write programs in it, but the understanding of what is happening during the execution of compiled code and its performance implications.

There are rare cases where we *really* need to switch to handwritten assembly for maximal performance, but most of the time compilers are capable of producing near-optimal code all by themselves. When they do not, it is usually because the programmer knows more about the problem than what can be inferred from the source code, but failed to communicate this extra information to the compiler.

In this section, we will discuss the intricacies of getting compiler to do exactly what we want and gathering useful information that can guide further optimizations.

## Stages of Compilation

Before jumping straight to compiler optimizations, let's recall the "big picture" first.

Skipping the boring parts, there are 4 stages of turning C programs into executables:

1. **Preprocessing** expands macros, pulls included source from header files, and stripps off comments from source code: `gcc -E souce.c` (outputs preprocessed source to stdout)
2. **Compiling** parses the source, checks for syntax errors, converts it into an immediate representation, performs optimizations, and finally translates it into assembly language: `gcc -S file.c` (emits an `.s` file)
3. **Assembly** turns it into machine code, except that external function calls like `printf` are substituted with placeholders: `gcc -c file.c` (emits an `.o` file, called *object file*)
4. **Linking** finally resolves the function calls by plugging in their actual addresses, and produces an executable binary: `gcc -o binary file.c`

Inspecting output from each of these stages can yield useful insights about what's happening.

You can get assembly from source by passing `-S` flag to the compiler, which will then generate a human-readable `*.s` file. If you pass `-fverbose-asm`, this file will also contain compiler comments about source code line numbers and some info about variables being used. If it is just a little snippet and you are feeling lazy, you can use [Compiler Explorer](https://godbolt.org/), which is an very handy online tool that converts source code to assembly, highlights logical asm blocks by color, includes a small x86 instruction set reference, and also has a large selection of other compilers, targets and languages.

Apart from assembly, the other most helpful level of abstraction is the *immediate representation* on which compilers perform optimizations. The IR defines the flow of computation itself and is much less dependent on architecture features like the number of registers or a particular instruction set. It is often useful to inspect these to get insight into how compiler *sees* your program, but this is a bit out of the scope of this chapter.

### Libraries and Interprocedural Optimization

We have the last stage, linking, because it is is both easier and faster — due to parallelism and caching of intermediate results — to compile programs on a file-by-file basis and then link those files together.

It also gives the ability to distribute code as *libraries*, which can be either *static* or *shared*:

- *Static* libraries are simply collections of precompiled object files that are merged with other sources by the compiler to produce a single executable, just as it normally would.
- *Dynamic* or *shared* libraries are precompiled executables that have additional meta-information about where its callables are, references to which are resolved during runtime. As the name suggests, this allows *sharing* the compiled binaries between multiple users.

To enable optimizations that involve more than one source file (function inlining, dead code elimination, etc.), modern compilers store immediate representation in object files as well, which allows them to perform *link-time optimization* by running certain lightweight optimizations that can benefit from having a larger context. This also allows using different compiled langauges in the same program, which can even be optimized accross language barriers if their compilers use the same intermediate representation.

LTO is a relatively recent feature (it appeared in GCC only around 2014), and it is still far from perfect. In C and C++, the way to make sure no performance is lost is to create a *header-only library*. As the name suggests, they are just header files that contain full definitions of all functions, and so by simply including them compiler gets access to all optimizations possible. Although you do have to recompile them completely each time, this approach makes sure no performance is lost.

## Compiler Optimizations

The first step of getting high performance from the compiler is to ask for it.

There are 4 *and a half* main levels of optimization for speed in GCC:

- `-O0` is the default one that does no optimizations (although, in a sense, it does optimize: for compilation time).
- `-O1` (also aliased as `-O`) does a few "low-hanging fruit" optimizations almost not affecting the compilation time.
- `-O2` enables all optimizations that are known to have little to no negative side effects and take reasonable time to complete (this is what most projects use for production builds).
- `-O3` does very aggressive optimization enabling almost all *correct* optimizations implemented in GCC.
- `-Ofast` does everything in `-O3` as well as adds a few more optimizations flags that may break strict standard compliance (e. g. floating-point operations may be rearranged so that the result is off by a fews bits of the mantissa).

The next thing you want to do is to tell the compiler more about the computer(s) this code is supposed to be run on: the smaller the set of platforms is, the better. By default it will generate binaries that can run on any relatively new (>2000) x86 CPU. The simplest way to narrow it down is to pass `-march` flag to specify the exact microarchitecture: `-march=haswell`. If you are compiling on the same computer that will run the binary, you can use `-march=native` for auto-detection.

The instruction sets are generally backwards-compatible, so it is often enough to use the name of the oldest microarchitecture you need to support, but a more robust approach is to list specific features that the CPU is guaranteed to have: `-mavx2`, `-mpopcount`. When you just want to tune a program for a particular machine without using any instructions that may break it on incompatible CPUs, you can use `-mtune` flag (by default `-march=x` also implies `-mtune=x`).

These options can also be specified for a compilation unit with pragmas instead of compilation flags:

```c++
#pragma GCC optimize("O3")
#pragma GCC target("avx2")
```

This is useful when you need to optimize a single high-performance procedure without increasing build time for the entire project.

### Situational Optimizations

Generally, you always want to specify the exact platform you are running and turn on `-O3`, but other optimizations, like the ones discussed [in the previous section](../assembly), are far more situational and require some input from the programmer.

**Loop unrolling** is disabled by default, unless the loop takes a small constant number of iterations known at compile time (in which case it will be replaced with a completely jump-free repeated sequence of instructions). It can be enabled with `-funroll-loops` flag, which will unroll all loops whose number of iterations can be determined at compile time or upon entry to the loop.

You can also use a pragma to target a specific loop:

```c++
#pragma GCC unroll 4
for (int i = 0; i < n; i++) {
    // ...
}
```

Loop unrolling makes binary larger, and may or may not make it run faster. Don't use it fanatically.

**Likeliness of branches** can be hinted by `[[likely]]` and `[[unlikely]]` attributes in ifs and switches:

```c++
int factorial(int n) {
    if (n > 1) [[likely]]
        return n * factorial(n - 1);
    else [[unlikely]]
        return 1;
}
```

This is a new feature that only appeared in C++20. Before that, there were GCC-specific `likely` and `unlikely` macros similarly used to wrap condition expressions:

```c++
int factorial(int n) {
    if (likely(n > 1))
        return n * factorial(n - 1);
    else
        return 1;
}
```

What it usually does is it swaps the branches so that the more likely one goes immediately after jump (recall that "don't jump" branch is taken by default). The performance gain is usually rather small, because for most hot spots hardware branch prediction works just fine.

**Inlining** is best left for the compiler to decide, but you can influence it with `inline` keyword:

```c++
inline int square(int x) {
    return x * x;
}
```

The hint may be ignored though if the compiler thinks that the performance gains are not be worth it. You can force inlining in GCC by adding `always_inline` attribute:

```c++
#define FORCE_INLINE inline __attribute__((always_inline))
```

There are many other cases like this when you need to point the compiler in the right direction, but we will get to them later when they become more relevant.

### Profile-Guided Optimization

Adding all this metadata to the source code is tedious. People already hate writing C++ even without having to do it.

It is also not always obvious whether certain optimizations are beneficial or not. To make a decision about branch reordering, inlining or unrolling, we need answers to questions like these:

- How often is this branch taken?
- How often is this function called?
- What is the average number of iterations in this loop?

Luckily for us, there is a way to provide this real-world information automatically.

*Profile-guided optimization* (PGO, also called "pogo" because it's easier and more fun to pronounce) is a technique that uses profiling data to improve performance beyond what can be achieved with just static analysis. In a nutshell, it involves adding timers and counters to the points of interest in the program, compiling and running it on real data, and then compiling it again, but this time supplying additional information from the test run.

The whole process is automated by modern compilers. For example, the `-fprofile-generate` flag will let GCC instrument the program with profiling code:

```
g++ -fprofile-generate [other flags] source.cc -o binary
```

After we run the program — preferrably on input that is as representive of real use case as possible — it will create a bunch of `*.gcda` files that contain log data for the test run, after which we can rebuild the program, but now adding the `-fprofile-use` flag:

```
g++ -fprofile-use [other flags] source.cc -o binary
```

It usually improves performance by 10-20% for large codebases, and for this reason it is commonly included in the build process of performance-critical projects. One more reason to invest in solid benchmarking code.

We will study how it works more deeply in the [next section](../profiling).

## What Compilers Can and Can't Do

Writing optimizing compilers is very hard. The last Turing award went to Alfred Aho and Jeffrey Ullman for [a 1000-page book](https://www.amazon.com/Compilers-Principles-Techniques-Tools-2nd/dp/0321486811/ref=pd_sbs_2?pd_rd_w=UZXK6&pf_rd_p=2419a049-62bf-452e-b0d0-ca5b7e35a7b4&pf_rd_r=AR7FPK4XQJD91HGS4PA3&pd_rd_r=2c8dc8d5-d0b8-40f3-b413-dbc23caaff70&pd_rd_wg=HsK5g&pd_rd_i=0321486811&psc=1) they wrote about compilers, which is considered an *introductory* textbook.

There are about 120 of optimizations in GCC included in `-O3`, and about 60 of them even have their own [Wikipedia pages](https://en.wikipedia.org/wiki/Category:Compiler_optimizations). At a very high level, these optimizations improve performance by:

- doing a good job at fundamental algorithms like register allocation, scheduling, dead code elimination, etc.;
- being good at eliminating unnecessary abstractions (inlining functions, eliminating temporary objects, etc);
- knowing the CPU architecture very well (replacing divisions by 2 with binary shifts, replacing multiply-and-add with `lea` when possible, and in general picking optimal instructions);
- knowing lots and lots of "tricks" (specific [peephole optimizations](https://en.wikipedia.org/wiki/Peephole_optimization) and loop transformations), and applying them whenever profitable.

Unless you are *really* into compiler engineering, I wouldn't recommend going through the list and learning all of them. Instead, gradually build up a broader understanding of what compilers are capable of. Trial and error generally works well here: just assume that everything generic and simple enough is already implemented, but always check assembly output in case you are wrong.

In general, when an optimization doesn't happen, it is usually because one of these three reasons:

- The compiler doesn't have enough information to know it will be beneficial.
- The optimization is actually not always correct: there is an input on which the result doesn't comply with the spec, even if it is correct on every input that the programmer expects.
- It isn't implemented in the compiler yet, either because it is too hard to implemenet in general, too costly to compute or too rare to be worth the troube (e. g. writing a tiny library for some specific algorithm is usually better than hardcoding it into compiler).

In addition, optimization sometimes fails just due to the source code being overly complicated.

### "Zero-cost" abstractions

In general, abstractions are great. Applied well, they reduce the amount of code and the mental burden of a programer.

But abstractions often come at a cost in terms of performance. When you use a shared library, you have spend some extra cycles moving data around to properly call its functions. When you call a virtual method, you can't reliably predict what code you are going to execute next and effectively suffer a branch mispredict.

Languages like C++ and Rust heavily promote the idea of *zero-cost* abstractions that have no extra runtime overhead, and that can be, at least in principle, completely removed by compilers. But in practice, there is no such thing as a zero-cost abstraction — compiler technology just isn't there yet.

Here is an example that personally bugs me: `std::min` from the C++ standard library. It repeatedly performs worse than just taking minimum by hands, the cause being that it isn't implemented just as `return (a < b ? a : b)`, but instead using variadic initializer lists and iterators for genericity:

```cpp
template<typename _Tp>
    _GLIBCXX14_CONSTEXPR
    inline _Tp
    min(initializer_list<_Tp> __l)
    { return *std::min_element(__l.begin(), __l.end()); }
```

Usually it isn't that hard to rewrite a small program so that it is more straightforward and closer to the hardware. If you start removing layers of abstractions the compiler will eventually give in.

Object-oriented and especially functional languages have some very hard-to-pierce abstractions like these. For this reason, people often prefer to write performance critical software (interpreters, runtimes, databases) in a style closer to C rather than higher-level languages.

### Memory aliasing

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

### Undefined Behavior

In safe langauges like Java and Rust, you normally have a well-defined behavior for every possible operation and every possible input. There are some things that are *underdefined*, like the order of keys in a hash table, but these are usually some minor details left to implementation for potential performance gains in the future.

In contrast, C and C++ take the concept of undefined behavior to another level. Certain operations don't cause an error during compilation or runtime but are just not *allowed* — in the sense of there being a contract between a programmer and a compiler, that in case of undefined behavior the compiler can do literally anything, including formatting your hard drive.

But compiler authors are not interested in formatting your hard drive of blowing up your monitor. Instead, undefined behavior is used to guarantee a lack of corner cases and help optimization.

For example, consider the case of signed overflow. On almost all architectures, signed integers overflow the same way as unsigned ones, with `INT_MAX + 1 == INT_MIN`, but yet this behavior is not a part of the C/C++ standard. This was very much intentional: if you disallow signed integer overflow, then `(x + 1) > x` is guaranteed to be always true for `int`, but not for `unsigned int`. For signed types, this allows compilers to optimize such checks away.

As a more naturally occuring example, consider the case of a loop with an integer control variable. C++ and Rust are advocating for using an unsigned integer (`size_t` / `usize`), while C programmers stubbornly keep using `int`. For a reason why, consider the following `for` loop:

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

When compiler can't prove inexistence of corner cases, but you can, you can use the machanism of undefined behavior to provide it with additional information. Clang has a helpful `__builtin_assume` function where you can put a statement that is guaranteed to be true, and compiler will use this assumption. In GCC you can do the same with `__builtin_unreachable`:

```cpp
void assume(bool pred) {
    if (!pred)
        __builtin_unreachable();
}
```

Then you can put `assume(k < vector.size())` before `at` and the bounds check should be optimized away.

### Arithmetic

Corner cases and tiny details are also something you should keep in mind when doing arithmetic. 

One example we've already mentioned before is the fact that floating-point arithmetic is not technically commutative, even though nobody cares about results being correct to the last bit. Compiler needs to comply with the C langauge spec regarding the order of operations, which blocks some potential optimizations. Strict compliance can be disabled with the `-ffast-math` flag, which is also included in `-Ofast`.

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

## Checklist

Usually the right approach to performance is to think how the main hotspots of the implementation should look like in assembly, write high-level code that resembles it as much as possible, and then repeatedly ask yourself the following questions until you are happy with its performance:

0. Does the compiler know it is allowed to do these optimizations? (`-O3`, `-march=native`, `-ffast-math`)
1. Are there any edge cases where optimized version would not work correctly? (use `__restrict__` and `const` keywords, try the `assume` trick)
2. Is there a real-world dataset for which the optimization may not be beneficial? (hints, pragmas, PGO)
3. Are there at least 1000 other places where this optimization makes sense? (remove abstractions and implement it manually, add a feature request for GCC and Clang)

In the majority of the cases, at least one of these answers will be "no", and then you will know what to do.
