---
title: What Compilers Can and Can't Do
weight: 10
draft: true
---

Let's sum up this chapter with a general advice.

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
- It isn't implemented in the compiler yet, either because it is too hard to implement in general, too costly to compute or too rare to be worth the trouble (e.g., writing a tiny library for some specific algorithm is usually better than hardcoding it into compiler).

In addition, optimization sometimes fails just due to the source code being overly complicated.

### Checklist

Usually the right approach to performance is to think how the main hot spots of the implementation should look like in assembly, write high-level code that resembles it as much as possible, and then repeatedly ask yourself the following questions until you are happy with its performance:

0. Does the compiler know it is allowed to do these optimizations? (`-O3`, `-march=native`, `-ffast-math`)
1. Are there any edge cases where optimized version would not work correctly? (use `__restrict__` and `const` keywords, try the `assume` trick)
2. Is there a real-world dataset for which the optimization may not be beneficial? (hints, pragmas, PGO)
3. Are there at least 1000 other places where this optimization makes sense? (remove abstractions and implement it manually, add a feature request for GCC and Clang)

In the majority of the cases, at least one of these answers will be "no," and then you will know what to do.
