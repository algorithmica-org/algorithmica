---
title: Stages of Compilation
weight: 1
---

Before jumping straight to compiler optimizations, which is what most of this chapter is about, let's briefly recap the "big picture" first. Skipping the boring parts, there are 4 stages of turning C programs into executables:

1. **Preprocessing** expands macros, pulls included source from header files, and strips off comments from source code: `gcc -E source.c` (outputs preprocessed source to stdout)
2. **Compiling** parses the source, checks for syntax errors, converts it into an intermediate representation, performs optimizations, and finally translates it into assembly language: `gcc -S file.c` (emits an `.s` file)
3. **Assembly** turns it into machine code, except that any external function calls like `printf` are substituted with placeholders: `gcc -c file.c` (emits an `.o` file, called *object file*)
4. **Linking** finally resolves the function calls by plugging in their actual addresses, and produces an executable binary: `gcc -o binary file.c`

Inspecting output from each of these stages can yield useful insights about what's happening in your program.

You can get assembly from source by passing `-S` flag to the compiler, which will then generate a human-readable `*.s` file. If you pass `-fverbose-asm`, this file will also contain compiler comments about source code line numbers and some info about variables being used. If it is just a little snippet and you are feeling lazy, you can use [Compiler Explorer](https://godbolt.org/), which is an very handy online tool that converts source code to assembly, highlights logical asm blocks by color, includes a small x86 instruction set reference, and also has a large selection of other compilers, targets and languages.

Apart from assembly, the other most helpful level of abstraction is the *intermediate representation* on which compilers perform optimizations. The IR defines the flow of computation itself and is much less dependent on architecture features like the number of registers or a particular instruction set. It is often useful to inspect these to get insight into how compiler *sees* your program, but this is a bit out of the scope of this book.

We will mainly use [GCC](https://gcc.gnu.org/) in this chapter, but also try to duplicate examples for [Clang](https://clang.llvm.org/) when necessary. The two compilers are largely compatible with each other, for the most part only differing in some optimization flags and minor syntax details.
