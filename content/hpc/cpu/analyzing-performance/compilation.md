---
title: Compiler Optimizations
weight: 2
---

The main benefit that comes from learning assembly language is not the ability to write programs in it, but the understanding of what is happening during the execution of *compiled* code and its performance implications.

There are rare cases where we really need to switch to handwritten assembly for maximal performance, but most of the time compilers are capable of producing near-optimal code by themselves. When they do not, it is usually because the programmer knows more about the problem than what can be inferred from the source code, but failed to communicate this extra information to the compiler.

In this section, we are going to discuss the intricacies of getting compiler to do exactly what we want, as well as gathering useful information that can guide further optimizations.

## Stages of Compilation

Skipping the boring parts, there are 4 stages of turning C programs into executables:

1. **Preprocessing** expands macros, pulls included source from header files, and stripps off comments from source code: `gcc -E souce.c` (outputs preprocessed source to stdout)
2. **Compiling** parses the source, checks for syntax errors, converts it into an immediate representation, performs optimizations, and finally translates it into assembly language: `gcc -S file.c` (emits an `.s` file)
3. **Assembly** essentially turns it into machine code, except that external function calls like `printf` are substituted with placeholders: `gcc -c file.c` (emits an `.o` file, called *object file*)
4. **Linking** finally resolves the function calls by plugging in their actual addresses, and produces an executable binary: `gcc -o binary file.c`

Inspecting output from each of these stages can yield useful insights about what's happening.

You can get assembly by passing `-S` flag to the compiler, which will then generate a human-readable `*.s` file. If you pass `-fverbose-asm`, this file will also contain compiler comments about source code line numbers and some info about variables being used. But if it is just a little snippet and you are feeling lazy, you can use [Compiler Explorer](https://godbolt.org/), which is an very handy online too that converts source to assembly, highlights logical asm blocks by color, includes a small x86 instruction set reference, and also has a large selection of other compilers, targets and languages.

Apart from assembly, the other most helpful level of abstraction is the *immediate representation* on which compilers perform optimizations. The IR defines the flow of computation itself and is much less dependent on architecture features like the number of registers or a particular instruction set. It is often useful to inspect these to get insight into how compiler *sees* your program, but this is a bit out of the scope of this book.

### Libraries and Interprocedural Optimization

We have the last stage, linking, because it is is both easier and faster — due to parallelism and caching of intermediate results — to compile programs on a file-by-file basis and then link those files together.

It also gives the ability to distribute code as *libraries*, which can be either *static* or *shared*:

- *Static* libraries are simply collections of precompiled object files that are merged with other sources by the compiler to produce a single executable, just as it normally would.
- *Dynamic* or *shared* libraries are precompiled executables that have additional meta-information about where its callables are, references to which are resolved during runtime. As the name suggests, this allows *sharing* the compiled binaries between multiple users.

To enable optimizations that involve more than one source file (function inlining, dead code elimination, etc.), modern compilers store immediate representation in object files as well, which allows them to perform *link-time optimization* by running certain lightweight optimizations that can benefit from having larger context. This also allows using different compiled langauges in the same program, which can even be optimized accross language barriers if their compilers use the same intermediate representation.

LTO is a relatively recent feature (it appeared in GCC only around 2014), and it is still far from perfect. In C and C++, the way to make sure no performance is lost is to create a header-only library, in which as the name suggests, full definitions of all functions are available in the header form and thus just included as source files by the program that uses them. Although you do have to recompile them completely each time, this makes sure no performance is lost.

## Negotiating with the Compiler

The first step of getting high performance from the compiler is to ask for it. There are 4 *and a half* main levels of optimization for speed in GCC:

- `-O0` is the default one that does no optimizations (although, in a sense, it does optimize, but for compile time)
- `-O1` (which is the same as `-O`) does a few "low hanging fruit" optimizations that almost don't affect compilation time
- `-O2` enables all optimizations that are known to have little to no negative side effects and take reasonable time to complete (this is what most projects use for production builds)
- `-O3` does very aggressive optimization enabling almost all *correct* optimizations implemented in GCC
- `-Ofast` does everything in `-O3` as well as a few more optimizations that may break strict standard compliance (e. g. floating-point operations may be rearranged so that the result is off by a fews bits of the mantissa)

Next thing you want to do is to tell the compiler more about the computer(s) this code is supposed to be run on: the smaller the set of platforms is, the better. By default it will generate binaries that can run on any relatively new x86-64 CPU. The simplest way to narrow it down is to pass `-march` flag to specify exact microarchitecture: `-march=haswell`. If you are compiling on the same computer that will run the binary, you can use `-march=native` for auto-detection.

The instruction sets are generally backwards-compatible, so it is often enough to use the name of the oldest microarchitecture you need to support, but a more robust approach is to list specific features that the CPU is guaranteed to have: `-mavx2`, `-mpopcount`. When you just want to tune a program for a particular machine without using any instructions that may break it on incompatible CPUs, you can use `-mtune` flag (by default `-march=x` also implies `-mtune=x`).

These options can also specified for a compilation unit with pragmas instead of compilation flags:

```c++
#pragma GCC optimize("O3")
#pragma GCC target("skylake") // <- doesn't work
```

This is useful when you need to optimize a single high-performance procedure without increasing build time for the entire project.

### Situational Optimizations

Generally, you always want to specify the exact platform you are running and turn on `-O3`, but other optimizations, like the ones discussed in the previous section, are far more situational and require input from the programmer.

**Loop unrolling** is disabled by default, unless the loop takes a small constant number of iterations known at compile time (in which case it will be replaced with a completely jump-free sequence of instructions). It can be enabled with `-funroll-loops` flag, which will unroll all loops whose number of iterations can be determined at compile time or upon entry to the loop.

Loop unrolling makes binary larger, and may or may not make it run faster. You can use a separate pragma to target a specific loop:

```c++
#pragma GCC unroll 4
for (int i = 0; i < n; i++) {
    // ...
}
```

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

**Inlining** is best left for the compiler to decide, but you can influence it with `inline` keyword:

```c++
inline int square(int x) {
    return x * x;
}
```

The hint may be ignored though, if the compiler thinks that the performance gains would not be worth it. You can force inlining in GCC by adding `always_inline` attribute:

```c++
#define FORCE_INLINE inline __attribute__((always_inline))
```

There are many other cases like this when you need to point the compiler in the right direction, but we will get to them later when they become more relevant.

## Profile-Guided Optimization

Adding all this metadata to the source code is tedious, and even without having to do it people already hate writing C++.

More over, it is not always obvious whether certain optimizations are beneficial or not. To make a decision, we need answers to questions like these:

- How often is this branch taken?
- How often is this function called?
- What is the average number of iterations in this loop?

Luckily for us, there is a way to provide this real-world information automatically.

*Profile-guided optimization* (PGO, also called "pogo" because it's easier and more fun to pronounce) is a technique of using profiling data to improve performance beyond what can be achieved with just static analysis. In a nutshell, it involves adding timers and counters to the points of interest in the program, compiling and running it on real data, and then compiling it again, but this time supplying additional information from the test run.

The whole process is automated by compilers. This will let GCC instrument the program with profiling code:

```
g++ -fprofile-generate [other flags] source.cc -o binary
```

After we run the program, preferrably on input that is as representive of real use case as possible, it will create a bunch of "*.gcda" files that contain log data for a test run, after which we can rebuild the program, but now with `-fprofile-use` flag:

```
g++ -fprofile-use [other flags] source.cc -o binary
```

It usually improves performance by 10-20% for large codebases, and for this reason it is commonly included in the build process of performance-critical projects. One more reason to invest in solid benchmarking code.

We will study how it works more deeply in the next section.

## What Compilers Can and Can't Do

Writing optimizing compilers is very hard. The last Turing award went to Alfred Aho and Jeffrey Ullman for [a 1000-page book](https://www.amazon.com/Compilers-Principles-Techniques-Tools-2nd/dp/0321486811/ref=pd_sbs_2?pd_rd_w=UZXK6&pf_rd_p=2419a049-62bf-452e-b0d0-ca5b7e35a7b4&pf_rd_r=AR7FPK4XQJD91HGS4PA3&pd_rd_r=2c8dc8d5-d0b8-40f3-b413-dbc23caaff70&pd_rd_wg=HsK5g&pd_rd_i=0321486811&psc=1) they wrote about compilers — and that is considered an *introductory* textbook.

There are about 120 of optimizations in GCC on `-O3`, and 60 of them even have their own [Wikipedia pages](https://en.wikipedia.org/wiki/Category:Compiler_optimizations). At a very high level, these optimizations can be grouped as:

- doing a good job at bread and butter algorithms like register allocation, scheduling, etc.
- being good at eliminating unnecessary abstractions (inlining functions, eliminating temporary objects in C++, etc)
- knowing the CPU architecture very well (replacing divisions by 2 by binary shifts, picking optimal instructions)
- knowing lots and lots of "tricks" (e.g. peephole optimizations, loop transformations, etc), and applying them whenever profitable

One example is hoisting computations out of the loop.

Removing dead code.


Unless you are really into compiler engineering, I would not recommend going through the list and learning all of them, but instead to build up a broader understanding of what compilers are capable of. Trial and error generally works well here: you can assume that everything generic and simple enough is already implemented, but check assembly output in case you are wrong. It usually isn't that hard to rewrite a loop in a way that is closer to hardware. If you start removing layers of abstractions, compiler will eventually give in.

It is hard to answer what compilers can do, instead it is easier to formulate what they can't do.

It is important to understand that if some optimizations doesn't work, it can only be because one of three reasons:

- The compiler doesn't have enough information to know it will be beneficial.
- The optimization is actually not always correct.
- It isn't implemented, either because it is too hard to implemenet in general, too costly to compute or too rare to be worth the troube.

I'm talking about the number of times somebody implements it by hand *and* it's useful.

However, it is important to understand that compilers are very conservative. They can't break the specification of the language, even if it will still be correct in 99% of the cases and the programmer expects it.

One example is floating-point arithmetic. Operations of addition and multiplication are commutative, but their rounding errors are not. Hence compilers won't be able to reorder them in a way that would speed things up. You can disable this with `-ffast-math`, which is also included in `-Ofast`.

A more complicated example is.

### Memory aliasing.

```c++
void add(int *a, int *b, int n) {
    for (int i = 0; i < n; i++)
        a[i] += b[i];
}
```

What if `a` and `b` intersect?

This is why we have `const` and `restrict` keywords. The first one promises (and also enforces) that we won't modify memory, and the second is a way to prime compiler that the memory we pointer to is guaranteed to be not aliased.

### Arithmetic


Optimizing arithmetic, like replacing multiplication and divison by 2 with bit shifts, as well as other known patterns. Known as peephole optimization

### Undefigned Behavior is Good

Another example is signed overflow. Compilers can do anything on UB, so they can optimize it the way they see fit.

It has to comply with the standard an perform overflows in a specific way.

(x + 1) > x is guaranteed to be true for int.

```
for (int i = 0; i <= n; i++) { /* ... */ }
```

This loop is guaranteed to complete, which removes check.

Overall, signed induction variables usually perform better than signed ones, despite what C++ STL and safety-obsessed languages like Rust teach us.


Transforming data structures to store as much as possible in registers.

There are more than a hundred of different optimizations (which you can look up in the [docs](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html), and compiler will also dump them all in one huge asm comment at the top of the file if you use `-fverbose-asm`).

The main limitation is that compilers have to act conservatively. Even if in 99% of use cases optimization will be correct, it isn't acceptable in other 1%.

It may replace .



Note that this does not always work. Consider the following case:

```c++
```

How many times does this loop execute? There are two valid answers: n/4 and infinity.

## Checklist

My point here is that the right mentality is to think of an implementation in assembly, write a high-level code that makes most sense, and then ask the following questions:

0. Does compiler know it can do it? (`-O3`, `-march=native`, `-ffast-math`)
1. Is there is any limitation or edge case where optimized version would not cut it? De-abstraction
2. Is there any condition in which the optimization is not beneficial? Hints, pragmas, PGO
3. Is it just you or are there 10000 similar places where it makes sense? Feature request, manual implementation

In majority of the cases, at least one of these answers will be "no", and you'll know what to do. If not, start going to lower level of abstraction.


build up a broader understanding of what compilers are capable of. Trial and error generally works well here: you can assume that everything generic and simple enough is already implemented, but check assembly output in case you are wrong. It usually isn't that hard to rewrite a loop in a way that is closer to hardware. If you start removing layers of abstractions, compiler will eventually give in.
