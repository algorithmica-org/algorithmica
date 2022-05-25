---
title: Integer Factorization
weight: 3
draft: true
---

The problem of factoring integers into primes is central to computational [number theory](/hpc/number-theory/). It has been [studied](https://www.cs.purdue.edu/homes/ssw/chapter3.pdf) since at least the 3rd century BC, and [many methods](https://en.wikipedia.org/wiki/Category:Integer_factorization_algorithms) have been developed that are efficient for different inputs.

In this case study, we specifically consider the factorization of *word-sized* integers: those on the order of $10^9$ and $10^{18}$. Untypical for this book, in this one, you may actually learn an asymptotically better algorithm: we start with a few basic approaches, and then gradually build up to the $O(\sqrt[4]{n})$-time *Pollard's rho algorithm* and optimize it to the point where it can factorize 60-bit semiprimes in 0.3-0.4ms, which is almost 4x faster than the previous state-of-the-art.

<!--
Integer factorization is interesting because of the RSA problem.
Unlike other case studies of this book, in this one you will actually learn an asymptotically better algorithm that you've never known before — Pollard's rho algorithm — which we optimize so that it is almost 4 times faster than the existing implementation, to the best of my knowledge.
-->

### Benchmark

For all methods, we will implement `find_factor` function that takes a positive integer $n$ and returns any of its non-trivial divisors (or `1` if the number is prime):

```c++
// I don't feel like typing "unsigned long long" each time
typedef __uint16_t u16;
typedef __uint32_t u32;
typedef __uint64_t u64;
typedef __uint128_t u128;

u64 find_factor(u64 n);
```

To find full factorization, you can apply it to $n$, reduce it, and continue until a new factor can no longer be found:

```c++
vector<u64> factorize(u64 n) {
    vector<u64> factorization;
    do {
        u64 d = find_factor(n);
        factorization.push_back(d);
        n /= d;
    } while (d != 1);
    return factorization;
}
```

Since after each removed factor the problem becomes considerably smaller and simpler, the worst-case running time of full factorization is equal to the worst-case running time of a `find_factor` call. 

For many factorization algorithms, including those presented in this article, the running time scales with the least prime factor. Therefore, to provide worst-case input, we use *semiprimes:* products of two prime numbers $p \le q$ that are on the same order of magnitude. To generate a $k$-bit semiprime, we generate two random $\lfloor k / 2 \rfloor$-bit primes.

Since some of the algorithms are inherently randomized, we also tolerate a small (<1%) percentage of false negative errors (when `find_factor` returns `1` despite number $n$ being composite), although this rate can be reduced to almost zero without significant performance penalties.

### Trial division

<!--

Trial division was first described by Fibonacci in 1202. Although it was probably known to animals. Perhaps some animals can factor? The scientific priority probably belongs to dinosaurs or ancient fish trying to divvy stuff up.

0.056024

-->

The most basic approach is to try every number less than $n$ as a divosor:

```c++
u64 find_factor(u64 n) {
    for (u64 d = 2; d < n; d++)
        if (n % d == 0)
            return d;
    return 1;
}
```

One simple optimization is to notice that it is enough to only check divisors that do not exceed $\sqrt n$. This works because if $n$ is divided by $d > \sqrt n$, then it is also divided by $\frac{n}{d} < \sqrt n$, so we can don't have to check it separately.

```c++
u64 find_factor(u64 n) {
    for (u64 d = 2; d * d <= n; d++)
        if (n % d == 0)
            return d;
    return 1;
}
```

In our benchmark, $n$ is a semiprime, and we always find the lesser divisor, so both $O(n)$ and $O(\sqrt n)$ implementations perform the same and are able to factorize ~2k 30-bit numbers per second, while taking whole ~20 seconds to factorize a single 60-bit number.

### Lookup Table

Nowadays, you can type `factor 57` in your Linux terminal or Google search bar to get the factorization of any number. But before computers were invented, it was more practical to use *factorization tables:* special books containing factorizations of the first $N$ numbers.

We can also use this approach to compute these lookup tables [during compile time](/hpc/compilation/precalc/). To save space, it is convenient to only store the smallest divisor of a number, requiring just one byte for a 16-bit integer:

```c++
template <int N = (1<<16)>
struct Precalc {
    unsigned char divisor[N];

    constexpr Precalc() : divisor{} {
        for (int i = 0; i < N; i++)
            divisor[i] = 1;
        for (int i = 2; i * i < N; i++)
            if (divisor[i] == 1)
                for (int k = i * i; k < N; k += i)
                    divisor[k] = i;
    }
};

constexpr Precalc P{};

u64 find_factor(u64 n) {
    return P.divisor[n];
}
```

This approach can process 3M 16-bit integers per second, although it [probably gets slower](../hpc/cpu-cache/bandwidth/) for larger numbers. While it requires just a few milliseconds and 64KB of memory to calculate and store the divisors of the first $2^{16}$ numbers, it does not scale well for larger inputs.

### Wheel factorization

To save paper space, pre-computer era factorization tables typically excluded numbers divisible by 2 and 5: in decimal numeral system, you can quickly determine whether a number is divisible by 2 or 5 (by looking at its last digit) and keep dividing the number $n$ by 2 or 5 while it is possible, eventually arriving to some entry in the factorization table. This makes the factorization table just ½ × ⅘ = 0.4 its original size.

We can apply a similar trick to trial division, first checking if the number is divisible by $2$, and then only check for odd divisors:

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

With 50% fewer divisions to do, this algorithm works twice as fast, but it can be extended. If the number is not divisible by $3$, we can also ignore all multiples of $3$, and the same goes for all other divisors. 

The problem is, as we increase the number of primes to exclude, it becomes less straightforward to iterate only over the numbers not divisible by them as they follow an irregular pattern — unless the number of primes is small. For example, if we consider $2$, $3$, and $5$, then, among the first $90$ numbers, we only need to check:

```center
(1,) 7, 11, 13, 17, 19, 23, 29,
31, 37, 41, 43, 47, 49, 53, 59,
61, 67, 71, 73, 77, 79, 83, 89…
```

You can notice a pattern: the sequence repeats itself every $30$ numbers because remainder modulo $2 \times 3 \times 5 = 30$ is all we need to determine whether a number is divisible by $2$, $3$, or $5$. This means that we only need to check $8$ specific numbers in every $30$, proportionally improving the performance:

```c++
u64 find_factor(u64 n) {
    for (u64 d : {2, 3, 5})
        if (n % d == 0)
            return d;
    u64 offsets[] = {0, 4, 6, 10, 12, 16, 22, 24};
    for (u64 d = 7; d * d <= n; d += 30) {
        for (u64 offset : offsets) {
            u64 x = d + offset;
            if (n % x == 0)
                return x;
        }
    }
    return 1;
}
```

As expected, it works $\frac{30}{8} = 3.75$ times faster than the naive trial division, processing about 7.6k 30-bit numbers per second. The performance can be improved by considering more primes, but the returns are diminishing: adding a new prime $p$ reduces the number of iterations by $\frac{1}{p}$, but increases the size of the skip-list by a factor of $p$, requiring proportionally more memory.

### Precomputed Primes

If we keep increasing the number of primes we exclude in wheel factorization, we eventually exclude all composite numbers and only check for prime factors. In this case, we don't need this array of offsets, but we need to precompute primes, which we can do during compile time like this:

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

This approach lets us process almost 20k 30-bit integers per second, but it does not work for larger (64-bit) numbers unless they have small ($< 2^{16}$) factors. Note that this is actually an asymptotic optimization: there are $O(\frac{n}{\ln n})$ primes among the first $n$ numbers, so this algorithm performs $O(\frac{\sqrt n}{\ln \sqrt n})$ operations, while wheel factorization only eliminates a large but fixed fraction of divisors. If we extend it to 64-bit numbers and precompute every prime under $2^{32}$ (storing which would require several hundred megabytes of memory), the relative speedup would grow by a factor of $\frac{\ln \sqrt{n^2}}{\ln \sqrt n} = 2 \cdot \frac{1/2}{1/2} \cdot \frac{\ln n}{\ln n} = 2$.

All variants of trial division, including this one, are bottlenecked by the speed of integer division, which can be [optimized](../hpc/arithmetic/division/) if we know the divisors in advice and allow for some precomputation:

```c++
// ...precomputation is the same as before,
// but we store the reciprocal instead of the prime number itself
u64 magic[6542];
// for each prime i:
magic[n_primes++] = u64(-1) / i + 1;

u64 find_factor(u64 n) {
    for (u64 m : P.magic)
        if (m * n < m)
            return u64(-1) / m + 1;
    return 1;
}
```

This makes the algorithm ~18x faster: we can now process ~350k 30-bit numbers per second. This is actually the most efficient algorithm we have 


$\tilde{O}(\sqrt n)$ territory

### Pollard's Rho Algorithm

---

```c++
u64 find_factor(u64 n) {
    while (true) {
        if (u64 g = gcd(randint(2, n - 1), n); g != 1)
            return g;
    }
}
```


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

### Larger Numbers

"How big are your numbers?" determines the method to use:


- Less than 2^16 or so: Lookup table.
- Less than 2^70 or so: Richard Brent's modification of Pollard's rho algorithm.
- Less than 10^50: Lenstra elliptic curve factorization
- Less than 10^100: Quadratic Sieve
- More than 10^100: General Number Field Sieve
