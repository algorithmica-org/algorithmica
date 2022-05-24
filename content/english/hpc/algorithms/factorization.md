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

0.056024
2043.968140

```c++
typedef __uint16_t u16;
typedef __uint32_t u32;
typedef __uint64_t u64;
typedef __uint128_t u128;

u64 find_factor(u64 n) {
    for (u64 d = 2; d * d <= n; d++)
        if (n % d == 0)
            return d;
    return 1;
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


---

If you have limited time, you should probably compute as much forward as possible, and then half the time computing the other.

How to optimize for the *average* case is unclear.

0.087907
3964.321045

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

0.199740
7615.217773

```c++
u64 find_factor(u64 n) {
    for (u64 d : {2, 3, 5})
        if (n % d == 0)
            return d;
    u64 increments[] = {0, 4, 6, 10, 12, 16, 22, 24};
    for (u64 d = 7; d * d <= n; d += 30) {
        for (u64 k = 0; k < 8; k++) {
            u64 x = d + increments[k];
            if (n % x == 0)
                return x;
        }
    }
    return 1;
}
```

19430.058594

```c++
const int N = (1 << 16);

struct Precalc {
    u16 primes[6542]; // # of primes under N=2^16

    constexpr Precalc() : primes{} {
        bool marked[N] = {};
        int n_primes = 0;

        for (int i = 2; i < N; i++) {
            if (!marked[i]) {
                primes[n_primes++] = i;
                for (int j = 2 * i; j < N; j += i)
                    marked[j] = true;
            }
        }
    }
};

constexpr Precalc P{};

u64 find_factor(u64 n) {
    for (u16 p : P.primes)
        if (n % p == 0)
            return p;
    return 1;
}
```

352997.656250

```c++
u64 magic[6542];
magic[n_primes++] = u64(-1) / i + 1;

u64 find_factor(u64 n) {
    for (u64 m : P.magic)
        if (m * n < m)
            return u64(-1) / m + 1;
    return 1;
}
```

Except that it is contant, so the speedup should be twice as much.

---

```c++
u64 find_factor(u64 n) {
    while (true) {
        if (u64 g = gcd(randint(2, n - 1), n); g != 1)
            return g;
    }
}
```

99.292641
25720.164062 almost 15x slower

```c++
u64 f(u64 x, u64 a, u64 mod) {
    return ((u128) x * x + a) % mod;
}

u64 diff(u64 a, u64 b) {
    // a and b are unsigned and so is their difference, so we can't just call abs(a - b)
    return a > b ? a - b : b - a;
}

u64 rho(u64 n, u64 x0 = 2, u64 a = 1) {
    u64 x = x0, y = x0, g = 1;
    while (g == 1) {
        x = f(x, a, n);
        y = f(y, a, n);
        y = f(y, a, n);
        g = gcd(diff(x, y));
    }
    return g;
}

u64 find_factor(u64 n) {
    return rho(n);
}
```

56.745281

```c++
u64 rho(u64 n, u64 x0 = 2, u64 a = 1) {
    u64 x = x0, y = x0;
    
    for (int l = 256; l < (1 << 20); l *= 2) {
        x = y;
        for (int i = 0; i < l; i++) {
            y = f(y, a, n);
            if (u64 g = gcd(diff(x, y), n); g != 1)
                return g;
        }
    }

    return 1;
}
```

426.389160

```c++
const int M = 1024;

u64 rho(u64 n, u64 x0 = 2, u64 a = 1) {
    u64 x = x0, y = x0, p = 1;
    
    for (int l = M; l < (1 << 20); l *= 2) {
        x = y;
        for (int i = 0; i < l; i += M) {
            for (int j = 0; j < M; j++) {
                y = f(y, a, n);
                p = (u128) p * diff(x, y) % n;
            }
            if (u64 g = gcd(p, n); g != 1)
                return g;
        }
    }

    return 1;
}
```

2948.260986

```c++
struct Montgomery {
    u64 n, nr;
    
    Montgomery(u64 n) : n(n) {
        nr = 1;
        for (int i = 0; i < 6; i++)
            nr *= 2 - n * nr;
    }

    u64 reduce(u128 x) const {
        u64 q = u64(x) * nr;
        u64 m = ((u128) q * n) >> 64;
        return (x >> 64) + n - m;
    }

    u64 multiply(u64 x, u64 y) {
        return reduce((u128) x * y);
    }
};

u64 f(u64 x, u64 a, Montgomery m) {
    return m.multiply(x, x) + a;
}

const int M = 1024;

u64 rho(u64 n, u64 x0 = 2, u64 a = 1) {
    Montgomery m(n);
    u64 y = x0;
    
    for (int l = M; l < (1 << 20); l *= 2) {
        u64 x = y, p = 1;
        for (int i = 0; i < l; i += M) {
            for (int j = 0; j < M; j++) {
                y = f(y, a, m);
                p = m.multiply(p, diff(x, y));
            }
            if (u64 g = gcd(p, n); g != 1)
                return g;
        }
    }

    return 1;
}
```

There are slightly more errors because we are a bit loose with modular arithmetic here. The error rate grows higher when we increase and decrease (due to overflows).

788.4861246275735
