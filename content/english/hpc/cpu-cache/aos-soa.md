---
title: AoS and SoA
weight: 13
---

It is often beneficial to group together the data you need to fetch at the same time: preferably, on the same or, if that isn't possible, neighboring cache lines. This improves the [spatial locality](/hpc/external-memory/locality) of your memory accesses, positively impacting the performance of memory-bound algorithms.

To demonstrate the potential effect of doing this, we modify the [pointer chasing](../latency) benchmark so that the next pointer is computed using not one, but a variable number of fields ($D$).

The first approach will locate these fields together as the rows of a two-dimensional array. We will refer to this variant as *array of structures* (AoS):

```c++
const int M = N / D; // # of memory accesses
int p[M], q[M][D];

iota(p, p + M, 0);
random_shuffle(p, p + M);

int k = p[M - 1];

for (int i = 0; i < M; i++)
    q[k][0] = p[i];

    for (int j = 1; j < D; j++)
        q[i][0] ^= (q[j][i] = rand());

    k = q[k][0];
}

for (int i = 0; i < M; i++) {
    int x = 0;
    for (int j = 0; j < D; j++)
        x ^= q[k][j];
    k = x;
}
```

And the second approach will place them in separately. The laziest way to do this is to transpose the two-dimensional array `q` and swap the indices in all its subsequent accesses:

```c++
int q[D][M];
//    ^--^
```

By analogy, we call this variant *structure of arrays* (SoA). Obviously, for large $D$'s, it performs much worse:

![](../img/aos-soa.svg)

The performance of both variants grows linearly with $D$, but AoS needs to fetch up to 16 times fewer total cache lines as the data is stored sequentially. Even when $D=64$, the additional time it takes to process the other 63 values is less than the latency of the first fetch.

You can also see the spikes at the powers of two. AoS performs slightly better because it can compute [horizontal xor-sum](/hpc/simd/reduction) faster with SIMD. In contrast, SoA performs much worse, but this isn't about $D$ being a power of two, but about $\lfloor N / D \rfloor$, the size of the second dimension, being a power of two, which in turn causes a pretty complicated [cache associativity](../associativity) effect.

Even though $N=2^{23}$ and the array is too big to fit into the L3 cache, to process some number of elements from different cache lines in parallel, you still need to store them somewhere temporarily — you can't simply use registers as there aren't enough of them. When `N / D` is a power of two and we are iterating over the array `q[D][N / D]` along the first index, all memory addresses will map to the same cache line, making many of them be re-fetched from upper layers of cache.

### RAM-Specific Timings

Let's do the same with the [padded int](../cache-lines)

Теперь мы добавили паддинг в AoS так, что каждый элемент теперь окружен 15 какими-то бесполезными элементами, а в остальном они все так же используются для подсчета ксор-суммы D чисел:

```c++
struct padded_int {
    int val;
    int padding[15];
};

const int M = N / D / 16;
padded_int q[M][D];
```


4D. На уровне RAM интереснее. Казалось бы, AoS-padded должна работать так же, как SoA: мы и там, и там загружаем 63 кэш-линий. Однако здесь играет роль то, как работает сама RAM.

Все данные в ней физически хранятся в виде двумерного массива конденсаторов, разделенного на строки и столбцы. Чтобы прочитать ячейку из него, нужно выполнить одно, два или три действия:

1. Прочитать содержимое строки в специальный временный буфер (row buffer).
2. Выбрать и собственно прочитать (или записать) в нем нужную ячейку.
3. И, опционально, записать данные из буфера обратно в строку массива — потому что чтение разрежает конденсаторы, и их нужно зарядить обратно. Этот шаг нужно делать только в том случае, если следующий доступ в память относится к какой-то другой строке.

Эти три шага занимают примерно одинаковое время. В AoS-padded все элементы хотя и распологаются в разных кэш-линиях, но эти линии соседние, и они с большой вероятностью окажутся в одной строчке в RAM, и первый и третий шаг можно проигнорировать. Поэтому суммарно все эти запросы отработают за втрое меньшее время (плюс задержка одного чтения)

![](../img/ram.png)

4C: когда мы падим инты, но оставляем суммарный размер массива таким же, ничего с точки зрения запросов к памяти и вычислений меняться не должно. Единственый нюанс: с паженными интами не происходит случайного шеринга кэша, как с обычными (когда мы загружаем какой-то инт, его соседи по кэш-линии тоже попадают в кэш), поэтому есть небольшое замедление.

![](../img/aos-soa-padded.svg)

![](../img/aos-soa-padded-n.svg)

The rest of the core is the same: the only difference is that they require a separate cache line access.

This is only specific to RAM: on array sizes that fit in cache, the benchmark is actually worse because the [cache sharing is worse](../cache-lines).

RAM timings.

This isn't about $D$ being equal to 64 but about $\lfloor \frac{N}{D} \rfloor$ being a large power of two.

TODO fix D and change N

### Temporary Storage Contention

We can turn on hugepages, and they make it 10 times worse (notice the logarithmic scale):

![](../img/soa-hugepages.svg)

This is a rare example where hugepages actually worsen performance. Usually they the latency by 10-15%, but here they make it 10x worse.

4F: Когда мы включаем большие страницы, задержка немного уменьшается — так же, как и в оригинальном бенчмарке задержки с D=1

4G: L1/L2 уровни кэша приватные для каждого ядра, и поэтому для простоты, чтобы не делать отдельно трансляцию адресов, для них везде используются виртуальные адреса, а не физические. На уровне L3 и RAM уже используются реальные, потому что иначе синхронизироваться никак не получится.

Когда мы используем 4K страницы, они размазываются по физической памяти довольно произвольным образом, и проблема описанная в 4E смягчается: все (физические) адреса имеют одинаковый остаток по модулю 4K, а не N/D. Когда мы запрашиваем именно большие страницы, они мапаются в последовательные же страницы в физической памяти, и поэтому этот лимит на максимальный alignment возрастает с 4K до 2M, и кэшам становится совсем плохо.

^ так что здесь ещё есть такой рандомный фактор, в зависимости от того, где операционная система страницы разместит

Это единственный известный мне пример, когда увеличение размера страницы ухудшает производительность, тем более в 10 раз
