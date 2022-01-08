---
title: Non-Zero-Cost Abstractions
weight: 7
---

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

Thick-bearded C/assembly programmers.
