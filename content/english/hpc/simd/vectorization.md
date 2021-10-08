---
title: (Auto-)Vectorization
weight: 2
---

Now, armed with a nicer syntax, consider a slightly more complex example: calculating the sum an array.

```c++
int sum_naive(int *a, int n) {
    int s = 0;
    for (int i = 0; i < n; i++)
        s += a[i];
    return s;
}
```

The naive approach is not so straightforward to vectorize, because the state of the loop (sum $s$ on the current prefix) depends on the previous iteration.

The way to overcome this is to split a single scalar accumulator $s$ into 8 separate ones, so that $s_i$ would contain the sum $\sum_{j=0}^{n / 8} a_{8 \cdot j + i }$, that is, the sum of every 8th element of the original array, shifted by $i$. If we store these 8 accumulators in a single 256-bit vector, we can update them all at once by adding consecutive 8-elements segments of the array:

```c++
int sum_simd(v8si *a, int n) {
    //       ^ you can just cast a pointer normally, like with any other pointer type
    v8si s = {0};

    for (int i = 0; i < n / 8; i++)
        s += a[i];
    
    int res = 0;
    
    // sum 8 accumulators into one 
    for (int i = 0; i < 8; i++)
        res += s[i];

    // add the remainder of a
    for (int i = n / 8 * 8; i < n; i++)
        res += a[i];
        
    return res;
}
```

The last part, where we sum up the 8 accumulators into a single scalar to get the total sum, can be done a bit faster by what's called "horizontal summation", which is the repeated use of [special instructions](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#techs=AVX,AVX2&text=_mm256_hadd_epi32&expand=2941) that add together pairs of adjacent elements:

```c++
int hsum(__m256i x) {
    __m128i l = _mm256_extracti128_si256(x, 0);
    __m128i h = _mm256_extracti128_si256(x, 1);
    l = _mm_add_epi32(l, h);
    l = _mm_hadd_epi32(l, l);
    return _mm_extract_epi32(l, 0) + _mm_extract_epi32(l, 1);
}
```

Although this is roughly how compilers vectorize it, this is not the fastest way to sums and other array reductions. We will come back to this problem in the last chapter.


### Memory Alignment

There are two ways to read / write a SIMD block from memory:

* `load` / `store` that segfault when the block doesn't fit a single cache line
* `loadu` / `storeu` that always work but are slower ("u" stands for unaligned)

When you can enforce aligned reads, always use the first one

**Выравнивание.** Отдельно стоит отметить одну деталь: операции чтения и записи имеют по две версии — `load` / `loadu` и `store` / `storeu`. Буква «u» здесь означает «unaligned» (англ. *невыровненный*). Первые корректно работают только тогда, когда весь считываемый блок помещается на одну кэш-линию (если это не так, то в рантаеме вызвется segfault), в то время как unaligned версия работает всегда и везде. 

Иногда, особенно когда операция «лёгкая», это отличие имеет большое значение — если не получается «выровнять» память, то производительность может резко упасть (хотя бы потому, что нужно загружать две кэш-линии вместо одной).

Например, так складывать два массива:

```c++
void aplusb_unaligned() {
    for (int i = 3; i + 7 < n; i += 8) {
        __m256i x = _mm256_loadu_si256((__m256i*) &a[i]);
        __m256i y = _mm256_loadu_si256((__m256i*) &b[i]);
        __m256i z = _mm256_add_epi32(x, y);
        _mm256_storeu_si256((__m256i*) &c[i], z);
    }
}
```

...будет на 30% медленнее, чем так:

```c++
void aplusb_aligned() {
    for (int i = 0; i < n; i += 8) {
        __m256i x = _mm256_load_si256((__m256i*) &a[i]);
        __m256i y = _mm256_load_si256((__m256i*) &b[i]);
        __m256i z = _mm256_add_epi32(x, y);
        _mm256_store_si256((__m256i*) &c[i], z);
    }
}
```

Если предположить, что в первом варианте начало массива совпадает с началом кэш-линии, а её размер 64 байта, то примерно половина `loadu` и `storeu` будут «плохими».

Вручную «выровнять» память для последовательного чтения через `load` в случае с массивами можно так:

So always ask compiler to align memory for you:

```c++
alignas(32) float a[n];

for (int i = 0; i < n; i += 8) {
    __m256 x = _mm256_load_ps(&a[i]);
    // ...
}
```

Указатель на начало массива теперь будет кратен 32 байтам, то есть размеру sse-блока. Теперь любое чтение и запись гарантированно будет внутри кэш-линии.

(This is also why compilers can't always auto-vectorize efficiently)




If you took some time to study the reference, you may have noticed that there are essentially two major groups of vector operations:

1. Instructions that perform some elementwise operation (`+`, `*`, `<`, `acos`, etc.).
2. Instructions that load, store, mask, shuffle and generally move data around.

While using the elementwise instructions is easy, the largest challenge with SIMD is getting the data in vector registers in the first place, preferrably with low enough overhead that makes the whole endeavor worthwhile.

## Loading Data

Intrinsics for reading and writing vector data have two versions: `load` / `loadu` and `store` / `storeu`. The letter "u" here stands for "unaligned". The difference is that the former ones only work correctly when the read / written block fits inside a single cache line (and crash otherwise), while the latter work regardless, albeit with a slight performance penalty if the block crosses a cache line.

As an extreme example, assuming that arrays `a`, `b` and `c` are all 32-bytes alligned, this code:

```c++
for (int i = 3; i + 7 < n; i += 8) {
    __m256i x = _mm256_loadu_si256((__m256i*) &a[i]);
    __m256i y = _mm256_loadu_si256((__m256i*) &b[i]);
    __m256i z = _mm256_add_epi32(x, y);
    _mm256_storeu_si256((__m256i*) &c[i], z);
}
```

...will be 30% slower than its aligned version:

```c++
for (int i = 0; i < n; i += 8) {
    __m256i x = _mm256_load_si256((__m256i*) &a[i]);
    __m256i y = _mm256_load_si256((__m256i*) &b[i]);
    __m256i z = _mm256_add_epi32(x, y);
    _mm256_store_si256((__m256i*) &c[i], z);
}
```

In the first version, roughly half of reads and writes will be "bad" because they cross a cache line boundary.

### Data Alignment

TODO: move it to memory chapter

`std::aligned_alloc`, that takes an alignment value and the size of array.


```c++
alignas(32) float a[n];

for (int i = 0; i < n; i += 8) {
    __m256 x = _mm256_load_ps(&a[i]);
    // ...
}
```

### Gather

In AVX2, you can also read non-continuous data using gather instructions.

These don't work 8 times faster though and are usually limited by memory rather than CPU, but they are still helpful with stuff like sparse linear algebra.

### Nontemporal Memory

These don't occupy cache line and work faster.

`stream`

## Masking

## Swizzling

## Lookup Tables



### AVX-512

In this book, we focus on AVX2, which should be available on 95% or desktop and server computers.

Algorithms specifically for AVX-512 are frequently published in blogs and research papers, so you would need to know the differences anyway. Here is a brief list of what AVX-512 extensions can do:

- Scattered writes
- "Compressed" writes


## Трудности автовекторизации

В самом начале статьи мы приводили пример кода, в котором уже оптимизированный бинарник получается без каких-либо изменений, кроме подключения нужного таргета компиляции. Зачем тогда вообще программисту делать что-либо ещё?

Дело в том, что иногда — очень редко — программист всё-таки умнее компилятора, потому что знает про задачу чуть больше.

Рассмотрим этот же пример, убрав из него всё лишнее:

```c++
void sum(int a[], int b[], int c[], int n) {
    for (int i = 0; i < n; i++)
        c[i] = a[i] + b[i];
}
```

Почему эту функцию нельзя заменить на векторизованный вариант автоматически?

Во-первых, потому что это не всегда корректно. Предположим, что `a[]` и `c[]` пересекаются, причём так, что указатели на начало массивов отличаются на 1-2 позиции. Ну, мало ли — может, мы такой изощрённой свёрткой хотели посчитать последовательность Фибоначчи. Тогда в simd-блоках данные будут пересекаться, и наблюдаемое поведение будет совсем не то, которое мы хотели.

Во-вторых, мы ничего не знаем про выравнивание этих массивов, и можем потерять производительность здесь (для больших циклов неактуально — компилятор оба «края» обрабатывает отдельными циклами).

На самом деле, когда компилятор подозревает, что функция будет использована для больших циклов, то на высоких уровнях оптимизации он сам вставит runtime-проверки на эти случаи и сгенерирует два разных варианта: через SSE и «безопасный».

Но выполнять эти проверки в рантайме не хочется, поэтому можно сообщить компилятору, что мы уверены, что ничего не сломается:

```c++
#pragma GCC ivdep
for (int i = 0; i < n; i++)
    // ...
```

Здесь «ivdep» означает **i**gnore **v**ector **dep**endencies — данные внутри цикла ни от чего не зависят.

Существует [много других способов](https://software.intel.com/sites/default/files/m/4/8/8/2/a/31848-CompilerAutovectorizationGuide.pdf) намекнуть компилятору, что конкретно мы имели в виду, но в сложных случаях — когда внутри цикла используются `if`-ы или вызываются какие-нибудь внешние функции — проще спуститься до уровня интринзиков и написать всё самому.

