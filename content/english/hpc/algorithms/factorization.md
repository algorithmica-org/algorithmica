---
title: Integer Factorization
weight: 3
draft: true
---

Integer factorization is interesting because of RSA problem.

"How big are your numbers?" determines the method to use:

- Less than 2^16 or so: Lookup table.
- Less than 2^70 or so: Richard Brent's modification of Pollard's rho algorithm.
- Less than 10^50: Lenstra elliptic curve factorization
- Less than 10^100: Quadratic Sieve
- More than 10^100: General Number Field Sieve


and do other computations such as computing the greatest common multiple (given that it is not even so that ) (since $\gcd(n, r) = 1$)

For all methods, we will implement `find_factor` function which returns one divisor ot 1. You can apply it recurively to get the factorization, so whatever asymptotic you had won't affect it:

```c++
typedef uint32_t u32;
typedef uint64_t u64;
typedef __uint128_t u128;

vector<u64> factorize(u64 n) {
    vector<u64> res;
    while (int d = find_factor(n); d > 1) // does it work?
        res.push_back(d);
    return res;
}
```

## Trial division

This is the most basic algorithm to find a prime factorization.

We divide by each possible divisor $d$.
We can notice, that it is impossible that all prime factors of a composite number $n$ are bigger than $\sqrt{n}$.
Therefore, we only need to test the divisors $2 \le d \le \sqrt{n}$, which gives us the prime factorization in $O(\sqrt{n})$.

The smallest divisor has to be a prime number.
We remove the factor from the number, and repeat the process.
If we cannot find any divisor in the range $[2; \sqrt{n}]$, then the number itself has to be prime.

```c++
u64 find_factor(u64 n) {
    for (u64 d = 2; d * d <= n; d++)
        if (n % d == 0)
            return d;
    return 1;
}
```

### Wheel factorization

This is an optimization of the trial division.
The idea is the following.
Once we know that the number is not divisible by 2, we don't need to check every other even number.
This leaves us with only $50\%$ of the numbers to check.
After checking 2, we can simply start with 3 and skip every other number.

```c++
u64 find_factor(u64 n) {
    if (n % 2 == 0)
        return 2;
    for (u64 d = 3; d * d <= n; d += 2)
        if (n % d == 0)
            return d;
    return 1;
}
```

This method can be extended.
If the number is not divisible by 3, we can also ignore all other multiples of 3 in the future computations.
So we only need to check the numbers $5, 7, 11, 13, 17, 19, 23, \dots$.
We can observe a pattern of these remaining numbers.
We need to check all numbers with $d \bmod 6 = 1$ and $d \bmod 6 = 5$.
So this leaves us with only $33.3\%$ percent of the numbers to check.
We can implement this by checking the primes 2 and 3 first, and then start checking with 5 and alternatively skip 1 or 3 numbers.

```c++
u64 find_factor(u64 n) {
    for (u64 d : {2, 3, 5})
        if (n % d == 0)
            return d;
    u64 increments[] =   {0, 4, 6, 10, 12, 16, 22, 24};
    u64 sum = 30;
    for (u64 d = 7; d * d <= n; d += sum) {
        for (u64 k = 0; k < 8; k++) {
            u64 x = d + increments[k];
            if (n % x == 0)
                return x;
        }
    }
    return 1;
}
```

We can extend this even further.
Here is an implementation for the prime number 2, 3 and 5.
It's convenient to use an array to store how much we have to skip.

### Lookup table

We will choose to store smallest factors of first $2^16$ — because this way they all fit in just one byte, so we are sort of saving on memory here.

```c++
template<int N = (1<<16)>
struct Precalc {
    char divisor[N];

    constexpr Precalc() : divisor{} {
        for (int i = 0; i < N; i++)
            divisor[i] = 1;
        for (int i = 2; i * i < N; i++)
            if (divisor[i] == 1)
                for (int k = i * i; k < N; k += i)
                    divisor[k] = i;
    }
};

constexpr Precalc precalc{};

u64 find_factor(u64 n) {
    return precalc.divisor[n];
}
```

### Pollard's Rho Algorithm

The algorithm is probabilistic. This means that it may or may not work. You would also need to 

Ро-алгоритм Полларда — рандомизированный алгоритм факторизации целых чисел, работающий за время $O(n^\frac{1}{4})$ и основывающийся не следствии из парадокса дней рождений:

> В мультимножество нужно добавить $O(\sqrt{n})$ случайных чисел от 1 до $n$, чтобы какие-то два совпали.

## $\rho$-алгоритм Полларда

Итак, мы хотим факторизовать число $n$. Предположим, что $n = p q$ и $p \approx q$. Понятно, что труднее случая, наверное, нет. Алгоритм итеративно ищет наименьший делитель и таким образом сводит задачу к как минимум в два раза меньшей.

Возьмём произвольную «достаточно случайную» с точки зрения теории чисел функцию. Например $f(x) = (x+1)^2 \mod n$.

Граф, в котором из каждой вершины есть единственное ребро $x \to f(x)$, называется *функциональным*. Если в нём нарисовать «траекторию» произвольного элемента — какой-то путь, превращающийся в цикл — то получится что-то похожее на букву $\rho$ (ро). Алгоритм из-за этого так и назван.

![](https://upload.wikimedia.org/wikipedia/commons/4/47/Pollard_rho_cycle.jpg)

Рассмотрим траекторию какого-нибудь элемента $x_0$: {$x_0$, $f(x_0)$, $f(f(x_0))$, $\ldots$}. Сделаем из неё новую последовательность, мысленно взяв каждый элемент по модулю $p$ — наименьшего из простых делителей $n$. 

**Утверждение**. Ожидаемая длина цикла в этой последовательности $O(\sqrt[4]{n})$.

*Доказательство:* так как $p$ — меньший делитель, то $p \leq \sqrt n$. Теперь просто подставлим в следствие из парадокса дней рождений: в множество нужно добавить $O(\sqrt{p}) = O(\sqrt[4]{n})$ элементов, чтобы какие-то два совпали, а значит последовательность зациклилась.

Если мы найдём цикл в такой последовательности — то есть такие $i$ и $j$, что $f^i(x_0) \equiv f^j(x_0) \pmod p$ — то мы сможем найти и какой-то делитель $n$, а именно $\gcd(|f^i(x_0) - f^j(x_0)|, n)$ — это число меньше $n$ и делится на $p$.

Алгоритм по сути находит цикл в этой последовательности, используя для этого стандартный алгоритм («черепаха и заяц»): будем поддерживать два удаляющихся друг от друга указателя $i$ и $j$ ($i = 2j$) и проверять, что $f^i(x_0) \equiv f^j(x_0) \pmod p$, что эквивалентно проверке $\gcd(|f^i(x_0) - f^j(x_0)|, n) \not \in \{ 1, n \}$.

```c++
typedef long long ll;

inline ll f(ll x) { return (x+1)*(x+1); }

ll find_divisor(ll n, ll seed = 1) {
    ll x = seed, y = seed;
    ll divisor = 1;
    while (divisor == 1 || divisor == n) {
        // двигаем первый указатель на шаг
        y = f(y) % n;
        // а второй -- на два
        x = f(f(x) % n) % n;
        // пытаемся найти общий делитель
        divisor = __gcd(abs(x-y), n);
    }
    return divisor;
}
```

Так как алгоритм рандомизированный, при полной реализации нужно учитывать разные детали. Например, что иногда делитель не находится (нужно запускать несколько раз), или что при попытке факторизовать простое число он будет работать за $O(\sqrt n)$ (нужно добавить отсечение по времени).

### Brent's Method

Another idea is to accumulate the product and instead of calculating GCD on each step to calculate it every log n steps.

### Optimizing division

The next step is to actually apply Montgomery Multiplication.

This is exactly the type of problem when we need specific knowledge, because we have 64-bit modulo by not-compile-constants, and compiler can't really do much to optimize it.

...

## Further optimizations

Существуют также [субэкспоненциальные](https://ru.wikipedia.org/wiki/%D0%A4%D0%B0%D0%BA%D1%82%D0%BE%D1%80%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D1%8F_%D1%86%D0%B5%D0%BB%D1%8B%D1%85_%D1%87%D0%B8%D1%81%D0%B5%D0%BB#%D0%A1%D1%83%D0%B1%D1%8D%D0%BA%D1%81%D0%BF%D0%BE%D0%BD%D0%B5%D0%BD%D1%86%D0%B8%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5_%D0%B0%D0%BB%D0%B3%D0%BE%D1%80%D0%B8%D1%82%D0%BC%D1%8B), но не полиномиальные алгоритмы факторизации. Человечество [умеет](https://en.wikipedia.org/wiki/Integer_factorization_records) факторизовывать числа порядка $2^{200}$.
