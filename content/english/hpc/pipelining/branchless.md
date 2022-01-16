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

В компиляторах есть способы, как сообщить, что бранч лучше заменить на cmov — __builtin_expect_with_probability(cond, true, 0.5) в GCC и __builtin_unpredictable(cond) в Clang — но оба теряются к тому моменту, когда оптимизатор решает, что выгоднее

https://bugs.llvm.org/show_bug.cgi?id=40027

Branching is expensive.

You can use cmov instructions. And something more complex in simd.

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


---

Интересные примеры из реального мира:

1. Упрощенно, внутри структуры std::string есть указатель на выделенный где-то null-terminated отрезок массива чаров и size_t размер строки. Очень частое значение для строк — пустая строка, которую тоже нужно как-то обрабатывать. Вместо того, чтобы записать в качестве указателя пустой строки nullptr и делать в коде дорогую проверку «не является ли строка пустой», в компиляторе GCC просто выделено специальное место, в которой лежит нулевой байт, на адрес которого ссылаются все нулевые строки. Все процедуры со строками вынуждены читать этот бесполезный нулевой байт, но это получается дешевле, чем делать проверку.

2. Бинарный поиск можно написать без бранчей, и на маленьких (влезающих в кэш) данных он будет работать в ~4 раза быстрее и стандартного самописного бинпоиска, и std::lower_bound — причем как чистый drop-in replacement, без какой-либо перестановки данных. Нет никаких серьёзных причин, почему обычный бинарный поиск компилятор не может оптимизировать сам — в GCC и LLVM заведены баги про это, но разработчики разных частей компилятора заявляют «это должно оптимизироваться не на этой стадии, а раньше/позже» и уже много лет перевешивают ответственность друг на друга
