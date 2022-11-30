---
title: Compilation
aliases: [/hpc/analyzing-performance/compilation]
weight: 4
---

The main benefit of [learning assembly language](../architecture/assembly) is not the ability to write programs in it, but the understanding of what is happening during the execution of compiled code and its performance implications.

There are rare cases where we *really* need to switch to handwritten assembly for maximal performance, but most of the time compilers are capable of producing near-optimal code all by themselves. When they do not, it is usually because the programmer knows more about the problem than what can be inferred from the source code but failed to communicate this extra information to the compiler.

In this chapter, we will discuss the intricacies of getting the compiler to do exactly what we want and gathering useful information that can guide further optimizations.
