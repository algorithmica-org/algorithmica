---
title: Bit Hacks and Arithmetic
weight: 3
---

## Integer Arithmetic

### Two's Complement

### Division and Modulo

**Деление.** В SSE нет операции деления  `int`-ов, но есть для `float`-ов и производных. Также нет взятия остатка от деления, что осложняет вычисления в комбинаторике.

Для деления 32-битных целых чисел их можно аккуратно скастовать к даблу, поделить так, и скастовать обратно — точности хватит, хоть это и будет медленно.

Умножение работает в несколько раз быстрее деления, и поэтому для ускорения деления `float`-ов на известную константу $d$ есть следующий [трюк](https://ridiculousfish.com/blog/posts/labor-of-division-episode-iii.html): заменить выражение $x / d$  на $x \cdot \frac{1}{d}$, и при этом $\frac{1}{d}$ посчитать во время компиляции.

Для целочисленных типов такое сделать немного сложнее — нужно заменить деление на умножение и битовый сдвиг. Для этого нужно приблизить $\frac{1}{d} \approx \frac{m}{2^s}$, подобрав «магическое» число $m$ и степень двойки $s$, такие что что `x / d == (x * m) >> s` для всех `x`.

Можно показать, что такая пара чисел всегда существует, и компилятор сам оптимизирует деление на константу подобным образом. Вот, например, сгенерированные инструкции для деления `unsigned long long` на $10^9 + 7$:

```nasm
movq    %rdi, %rax
movabsq $-8543223828751151131, %rdx ; загружает магическую константу в регистр
mulq    %rdx                        ; делает умножение
movq    %rdx, %rax
shrq    $29, %rax                   ; делает битовый сдвиг результата
```

Здесь для умножения используется «mixed precision» инструкция `mulq`, которая берёт два 64-битных числа и записывает 128-битный результат их умножения в два 64-битных регистра (lo, hi).

Для деления `long`-ов на SSE такой способ пока что не работает: аналогичная инструкция добавилась только в AVX512.

## Floating-Point Arithmetic

sign, mantissa, exponent

bfloat, float, double

errors, associativity

`-ffast-math`

## Bit Hacks

### Mask Operations

### Special Instructions

`popcnt`

leading / trailing zeros

x & (x - 1)

`__log` as trailing zeros rounded down logarithm

## Hash Functions

Cryptographic and non-cryptographic

SHA-1, MD5

MurMurHash
CRC32

## Randomness
