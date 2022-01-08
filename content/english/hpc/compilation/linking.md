---
title: Interprocedural Optimization
weight: 3
---

<!-- static linking flag -->

We have the last stage, linking, because it is is both easier and faster — due to parallelism and caching of intermediate results — to compile programs on a file-by-file basis and then link those files together.

It also gives the ability to distribute code as *libraries*, which can be either *static* or *shared*:

- *Static* libraries are simply collections of precompiled object files that are merged with other sources by the compiler to produce a single executable, just as it normally would.
- *Dynamic* or *shared* libraries are precompiled executables that have additional meta-information about where its callables are, references to which are resolved during runtime. As the name suggests, this allows *sharing* the compiled binaries between multiple users.

To enable optimizations that involve more than one source file (function inlining, dead code elimination, etc.), modern compilers store intermediate representation in object files as well, which allows them to perform *link-time optimization* by running certain lightweight optimizations that can benefit from having a larger context. This also allows using different compiled languages in the same program, which can even be optimized across language barriers if their compilers use the same intermediate representation.

LTO is a relatively recent feature (it appeared in GCC only around 2014), and it is still far from perfect. In C and C++, the way to make sure no performance is lost is to create a *header-only library*. As the name suggests, they are just header files that contain full definitions of all functions, and so by simply including them compiler gets access to all optimizations possible. Although you do have to recompile them completely each time, this approach makes sure no performance is lost.