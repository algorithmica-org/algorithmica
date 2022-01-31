---
title: Non-Zero-Cost Abstractions
weight: 7
draft: true
---

In general, abstractions are great. Applied well, they reduce the amount of code and the mental burden of a programer.

But abstractions often come at a cost in terms of performance. When you use a shared library, you have spend some extra cycles moving data around to properly call its functions. When you call a virtual method, you can't reliably predict what code you are going to execute next and effectively suffer a branch mispredict.

Languages like C++ and Rust heavily promote the idea of *zero-cost* abstractions that have no extra runtime overhead, and that can be, at least in principle, completely removed by compilers. But in practice, there is no such thing as a zero-cost abstraction — compiler technology just isn't there yet.

**Virtual functions.** Any type of runtime polymorphism.

**Bounds checking.** Compilers are good at eliminating them though.

**Generally any complicated code.** Here is an example that personally bugs me: `std::min` from the C++ standard library. It repeatedly performs worse than just taking minimum by hands, the cause being that it isn't implemented just as `return (a < b ? a : b)`, but instead using variadic initializer lists and iterators for genericity:

```cpp
template<typename _Tp> GLIBCXX14_CONSTEXPR inline _Tp min(initializer_list<_Tp> __l) {
    return *std::min_element(__l.begin(), __l.end());
}
```

Usually it isn't that hard to rewrite a small program so that it is more straightforward and closer to the hardware. If you start removing layers of abstractions the compiler will eventually give in.

Object-oriented and especially functional languages have some very hard-to-pierce abstractions like these. For this reason, people often prefer to write performance critical software (interpreters, runtimes, databases) in a style closer to C rather than higher-level languages.

Thick-bearded C/assembly programmers.

### Memory

Pointer chasing.

```c++
typedef vector< vector<int> > matrix;
matrix a(n, vector<int>(n, 0));

int val = a[i][j];
```

This is up tow twice as slow: you first need to fetch 

```c++
int a = new int[n * n];
memset(a, 0, 4 * n* n);

int val = a[i * n + j];
```

You can write a wrapper is you really want an abstraction:

```c++
template<typename T>
struct Matrix {
    int x, y, n, N;
    T* data;
    T* operator[](int i) { return data + (x + i) * N + y; }
};
```

For example, the [cache-oblivious transposition](/hpc/external-memory/oblivious) would go like this:

```c++
Matrix<T> subset(int _x, int _y, int _n) { return {_n, _x, _y, N, data}; }

Matrix<T> transpose() {
    if (n <= 32) {
        for (int i = 0; i < n; i++)
            for (int j = 0; j < i; j++)
                swap((*this)[j][i], (*this)[i][j]);
    } else {
        auto A = subset(x, y, n / 2).transpose();
        auto B = subset(x + n / 2, y, n / 2).transpose();
        auto C = subset(x, y + n / 2, n / 2).transpose();
        auto D = subset(x + n / 2, y + n / 2, n / 2).transpose();
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                swap(B[i][j], C[i][j]);
    }

    return *this;
}
```

I personally prefer to write low-level code, because it is easier to optimize.

It is cleaner? Don't think so.
