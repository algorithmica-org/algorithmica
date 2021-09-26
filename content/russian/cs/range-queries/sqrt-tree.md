---
title: sqrt-дерево
authors:
- Горюнов Григорий
- "[Александр Керножицкий](https://codeforces.com/blog/entry/57046)"
weight: 7
draft: true
---

Дан массив $a$ из $n$ элементов и ассоциативная операция $\circ$: $(x \circ y) \circ z = x \circ (y \circ z) \forall x, y, z$.

Такими операциями являются, к примеру, $\gcd$, $\min$, $\max$, $+$, $\text{and}$, $\text{or}$, $\text{xor}$.

Также, даны запросы $q(l, r)$. Для каждого запроса необходимо посчитать $a_l \circ a_{l+1} \circ \dots \circ a_r$.

sqrt-дерево может отвечать на такие запросы за $O(1)$ с препроцессингом за $O(n\log\log n)$ времени и затратами в $O(n\log\log n)$ памяти.

## Описание

### Построение корневой декомпозиции

Построим корневую декомпозицию. Разделим массив на $\sqrt n$ блоков, каждый размером $\sqrt n$. Для каждого блока посчитаем:

1. Ответы на запросы, которые полностью лежат в данном блоке и начинаются в начале блока ($\text{prefixOp}$)
2. Ответы на запросы, которые полностью лежат в данном блоке и заканчиваются в конце блока ($\text{suffixOp}$)

Также рассчитаем следующий массив:

3. $\text{between}_{i, j}$ (для $i \le j$) --- ответ на запрос который начинается в начале блока $i$ и заканчивается в конце блока $j$. Поскольку у нас $\sqrt n$ блоков, размер этого массива будет $O( \sqrt{n}^2 ) = O(n)$.

Рассмотрим пример.

Пусть $\circ$ --- это $+$, то есть у нас запросы суммы на отрезке и дан следующий массив $a$: `{1, 2, 3, 4, 5, 6, 7, 8, 9}`

Он будет разделен на 3 блока: `{1, 2, 3}`, `{4, 5, 6}` и `{7, 8, 9}`.

Для 1 блока $\text{prefixOp}$ равен `{1, 3, 6}` и $\text{suffixOp}$ равен `{6, 5, 3}`.

Для 2 блока $\text{prefixOp}$ равен `{4, 9, 15}` и $\text{suffixOp}$ равен `{15, 11, 6}`.

Для 3 блока $\text{prefixOp}$ равен `{7, 15, 24}` и $\text{suffixOp}$ равен `{24, 17, 9}`.

Массив $\text{between}$ (элементы, для которых $i > j$ заполнены нулями):
```
{ {6, 21, 45},
  {0, 15, 39},
  {0, 0,  24} }
```

Очевидно, что эти массивы можно легко посчитать за $O(n)$ времени и $O(n)$ памяти.

На некоторые запросы ответить можно прямо сейчас. Если запрос не находится целиком в одном блоке, то кго можно разделить на три части: суффикс какого-то блока (он же левый obroobock), отрезок последовательных блоков и префикс какого-то блока (он же правый obroobock). Тогда ответом на запрос будет объединение значения из $\text{suffixOp}$, задем значения из $\text{between}$ и потом значения из $\text{prefixOp}$.

Но если есть запросы, которые полностью лежат в одном блоке, то с помощью этих массивов их нельзя обработать. Необходимо что-то придумать (Если операция обратимая, то можно сделать для каждого блока массив $\text{undo}$: значение обратной операции на суффиксе. Тогда ответом на запрос будет $\text{suffixOp}(i) \circ \text{undo}(j+1)$).

### Делаем дерево

Нельзя ответить _только_ на запросы, которые ледат полностью в одном блоке. Что, если **построить sqrt-дерево в каждом блоке**? Так делать можно. И если делать это рекурсивно, пока размер блока не будет равен 1 или 2. Для таких блоков ответ на запрос можно легко посчитать за $O(1)$.

Итак, у нас есть дерево. Каждая вершина дерева отображает какой-то подотресок массива. У вершины с подотрезком длины $k$ будет $\sqrt k$ детей -- на каждый блок. Также каждая вершина содержит три описанных ранее массива для своего отрезка. Корень дерева отображает весь массив. Листьями являются вершины с отрезками длины 1 или 2.

Также очевидно, что высота этого дерева $O(\log\log n)$, поскольку если какая-то вершина отображает отрезок длины $k$, то длина отрезков ее детей $\sqrt k$. $\log {\sqrt k} = \displaystyle\frac{\log k}{2}$, то есть $\log k$ с каждым уровнем уменьшается в два раза, а тогда высота дерева равна $O(\log\log n)$. Время на построение и использование памяти будут $O(n\log\log n)$, так как каждый элемент на каждом уровне встречается только один раз.

Теперь на запросы можно отвечать за $O(\log\log n)$: идем вниз по дереву, пока не наткнемся на отрезок длины 1 или 2 или не встретим первый отрезок, на котором запрос не помещается весь в один блок. Как отвечать на запрос в таком случае было объяснено ранее.

Хорошо, мы научились отвечать на запросы за $O(\log\log n)$. Можно ещё быстрее?

### Оптимизации ответа на запрос

Одна из наиболее очевидных оптимизаций --- двоичным поиском найти вершину дерева, которая будет нужна. Используя двоичный поиск можно добиться асимптотики $O(\log\log\log n)$ на запрос. Можно ли _ещё_ быстрее?

Да, можно. Давайте сделаем следующие предположения:

1. Размер каждого блока --- степень двойки.
2. На каждом уровне все блоки имеют одинаковый размер.

Чтобы этого достичь, добавим нейтральных элементов в конец массива, чтобы его размер стал степенью 2.

При таком подходе длины отрезков, соответствующих некоторым блокам, могут увеличиться почти в два раза чтобы стать степенью 2, но эта длина все равно остается $O(\sqrt{k})$ и построение массивов на отрезке остается линейным.

Теперь легко проверить, что запрос целиком лежит в блоке размера $2^k$. Запишем отрезок запроса в 0-индексации в двоичном виде. Пусть $k=4$, $l=39$, $r=46$, тогда

$l = 39_{10} = 100111_2$

$r = 46_{10} = 101110_2$

Блоки на одном уровне имеют одинаковый размер (в нашем случае $2^k = 2^4 = 16$) и полностью покрывают массив, так что первый блок покрывает элементы $[0; 16)$ ($(000000_2 - 001111_2)$ в двоичном виде), второй --- $[16; 32)$ ($(010000_2 - 011111_2)$ в двоичном виде) и так далее. Видно, что индексы элементов в одном блоке отличаются только в $k$ (в нашем случае 4) младших битах. В нашем случае у $l$ и $r$ биты сопадают, за исключением 4 младших, поэтому они лежат в одном блоке.

Итак, необходимо проверить, что отличаются не более $k$ младших битов, то есть $l \oplus r < 2^k$.

С этими наблюдениями легко понять, какой уровень необходим для быстрого ответа на запрос. Вот как это делается:

1. Для каждого $i$ не превышающего размер массива найдем старший единичный бит. Чтобы это делать быстро, воспользуемся динамикой и предпросчитанным массивом.
2. Для каждого $q(l, r)$ найдем старший бит $l \oplus r$ и, используя эту информацию, легко определить уровень запроса. Тут тоже можно воспользоваться предпросчетом.

Больше подробностей в исходном коде ниже.

Итак, мы добились ответа на запрос за $O(1)$. Ура!

```cpp
int op(int a, int b);

inline int log2Up(int n) {
  int res = 0;
  while ((1 << res) < n) {
    res++;
  }
  return res;
}

class SqrtTree {
private:
  int n, lg;
  vector<int> v;
  vector<int> clz;
  vector<int> layers;
  vector<int> onLayer;
  vector< vector<int> > pref;
  vector< vector<int> > suf;
  vector< vector<int> > between;
  
  void build(int layer, int lBound, int rBound) {
    if (layer >= (int)layers.size()) {
      return;
    }
    int bSzLog = (layers[layer]+1) >> 1;
    int bCntLog = layers[layer] >> 1;
    int bSz = 1 << bSzLog;
    int bCnt = 0;
    for (int l = lBound; l < rBound; l += bSz) {
      bCnt++;
      int r = min(l + bSz, rBound);
      pref[layer][l] = v[l];
      for (int i = l+1; i < r; i++) {
        pref[layer][i] = op(pref[layer][i-1], v[i]);
      }
      suf[layer][r-1] = v[r-1];
      for (int i = r-2; i >= l; i--) {
        suf[layer][i] = op(v[i], suf[layer][i+1]);
      }
      build(layer+1, l, r);
    }
    for (int i = 0; i < bCnt; i++) {
      int ans = 0;
      for (int j = i; j < bCnt; j++) {
        int add = suf[layer][lBound + (j << bSzLog)];
        ans = (i == j) ? add : op(ans, add);
        between[layer][lBound + (i << bCntLog) + j] = ans;
      }
    }
  }
public:
  inline int query(int l, int r) {
    if (l == r) {
      return v[l];
    }
    if (l + 1 == r) {
      return op(v[l], v[r]);
    }
    int layer = onLayer[clz[l ^ r]];
    int bSzLog = (layers[layer]+1) >> 1;
    int bCntLog = layers[layer] >> 1;
    int lBound = (l >> layers[layer]) << layers[layer];
    int lBlock = ((l - lBound) >> bSzLog) + 1;
    int rBlock = ((r - lBound) >> bSzLog) - 1;
    int ans = suf[layer][l];
    if (lBlock <= rBlock) {
      ans = op(ans, between[layer][lBound + (lBlock << bCntLog) + rBlock]);
    }
    ans = op(ans, pref[layer][r]);
    return ans;
  }
  
  SqrtTree(const vector<int>& v)
    : n((int)v.size()), lg(log2Up(n)), v(v), clz(1 << lg), onLayer(lg+1) {
    clz[0] = 0;
    for (int i = 1; i < (int)clz.size(); i++) {
      clz[i] = clz[i >> 1] + 1;
    }
    int tlg = lg;
    while (tlg > 1) {
      onLayer[tlg] = (int)layers.size();
      layers.push_back(tlg);
      tlg = (tlg+1) >> 1;
    }
    for (int i = lg-1; i >= 0; i--) {
      onLayer[i] = max(onLayer[i], onLayer[i+1]);
    }
    pref.assign(layers.size(), vector<int>(n));
    suf.assign(layers.size(), vector<int>(n));
    between.assign(layers.size(), vector<int>(1 << lg));
    build(0, 0, n);
  }
};
```

## Обновление элементов

sqrt-дерево поддерживает операции обновления --- отдельного элемента и на подотрезке.

### Обновление одного элемента

Рассмотрим запрос обновления $\text{update}(x, val)$, который выполняет присваивание $a_x = val$. Необходимо выполнять этот запрос достаточно быстро.

#### Наивный подход

Посмотрим на то, что меняется в дереве при изменении одного элемента. Рассмотрим вершину дерева с длиной $l$ и ее массивы: $\text{prefixOp}$, $\text{suffixOp}$ и $\text{between}$. Легко заметить, что только $O(\sqrt{l})$ элементов $\text{prefixOp}$ и $\text{suffixOp}$ меняются --- элементы внутри измененного блока. $O(l)$ элементов изменятся в массиве $\text{between}$. Всего в вершине обновлено $O(l)$ элементов.

Каждый элемент встречается на каждом слое, и всего один раз на слой. Длина корня (уровень 0) --- $O(n)$, у вершин на уровне 1 длина $O(\sqrt{n})$, на уровне 2 -- $O(\sqrt{\sqrt{n}})$, и так далее. Таким образом сложность запроса обновления $O(n + \sqrt{n} + \sqrt{\sqrt{n}} + \dots) = O(n)$.

Слишком медленно. Можно быстрее?

#### sqrt-дерево в sqrt-дереве

Заметим, что узкое место в обновлении --- перестроение $\text{between}$ в корне дерева. Чтобы соптимизировать дерево, избавимся от этого массива! Вместо массива $\text{between}$ сделаем другое sqrt-дерево в корневой вершине. Назовем его $\text{index}$. Оно будет выполнять ту же роль, что и массив $\text{between}$ --- ответ на запрос на отрезкахх блоков. $\text{index}$ используется только в корневой вершине, остальные вершины сохраняют свои массивы $\text{between}$.

Назовем sqrt-дерево _индексированным_, если у его корня есть массив $\text{index}$. sqrt-дерево с массивом $\text{between}$ в корне --- _неиндексированным_. Заметьте, что $\text{index}$ **является _неиндексированным_**.

Итак, алгоритм обновления для _индексированного_ дерева:

1. Обновить $\text{prefixOp}$ и $\text{suffixOp}$ за $O(\sqrt{n})$.

2. Обновить $\text{index}$. Его длина -- $O(\sqrt{n})$, необходимо обновить только один элемент (тот, который соответствует измененному блоку). Асимптотика этого шага --- $O(\sqrt{n})$. Чтобы это сделать, можно использовать "медленный" алгоритм, приведенный в начале раздела.

3. Перейти в дочернюю вершину, соответствующую измененному блоку, и обновить ее "медленным" алгоритмом за $O(\sqrt{n})$.

Асимптотика запроса так и осталась $O(1)$: необходимо использовать $\text{index}$ не более одного раза на запрос, а обращение к нему работает за $O(1)$.

Таким образом, асимптотика обновления одного элемента $O(\sqrt{n})$. Ура!

Код:

```
SqrtTreeItem op(const SqrtTreeItem &a, const SqrtTreeItem &b);

inline int log2Up(int n) {
  int res = 0;
  while ((1 << res) < n) {
    res++;
  }
  return res;
}

class SqrtTree {
private:
  int n, lg, indexSz;
  vector<SqrtTreeItem> v;
  vector<int> clz, layers, onLayer;
  vector< vector<SqrtTreeItem> > pref, suf, between;
  
  inline void buildBlock(int layer, int l, int r) {
    pref[layer][l] = v[l];
    for (int i = l+1; i < r; i++) {
      pref[layer][i] = op(pref[layer][i-1], v[i]);
    }
    suf[layer][r-1] = v[r-1];
    for (int i = r-2; i >= l; i--) {
      suf[layer][i] = op(v[i], suf[layer][i+1]);
    }
  }
  
  inline void buildBetween(int layer, int lBound, int rBound, int betweenOffs) {
    int bSzLog = (layers[layer]+1) >> 1;
    int bCntLog = layers[layer] >> 1;
    int bSz = 1 << bSzLog;
    int bCnt = (rBound - lBound + bSz - 1) >> bSzLog;
    for (int i = 0; i < bCnt; i++) {
      SqrtTreeItem ans;
      for (int j = i; j < bCnt; j++) {
        SqrtTreeItem add = suf[layer][lBound + (j << bSzLog)];
        ans = (i == j) ? add : op(ans, add);
        between[layer-1][betweenOffs + lBound + (i << bCntLog) + j] = ans;
      }
    }
  }
  
  inline void buildBetweenZero() {
    int bSzLog = (lg+1) >> 1;
    for (int i = 0; i < indexSz; i++) {
      v[n+i] = suf[0][i << bSzLog];
    }
    build(1, n, n + indexSz, (1 << lg) - n);
  }
  
  inline void updateBetweenZero(int bid) {
    int bSzLog = (lg+1) >> 1;
    v[n+bid] = suf[0][bid << bSzLog];
    update(1, n, n + indexSz, (1 << lg) - n, n+bid);
  }
  
  void build(int layer, int lBound, int rBound, int betweenOffs) {
    if (layer >= (int)layers.size()) {
      return;
    }
    int bSz = 1 << ((layers[layer]+1) >> 1);
    for (int l = lBound; l < rBound; l += bSz) {
      int r = min(l + bSz, rBound);
      buildBlock(layer, l, r);
      build(layer+1, l, r, betweenOffs);
    }
    if (layer == 0) {
      buildBetweenZero();
    } else {
      buildBetween(layer, lBound, rBound, betweenOffs);
    }
  }
  
  void update(int layer, int lBound, int rBound, int betweenOffs, int x) {
    if (layer >= (int)layers.size()) {
      return;
    }
    int bSzLog = (layers[layer]+1) >> 1;
    int bSz = 1 << bSzLog;
    int blockIdx = (x - lBound) >> bSzLog;
    int l = lBound + (blockIdx << bSzLog);
    int r = min(l + bSz, rBound);
    buildBlock(layer, l, r);
    if (layer == 0) {
      updateBetweenZero(blockIdx);
    } else {
      buildBetween(layer, lBound, rBound, betweenOffs);
    }
    update(layer+1, l, r, betweenOffs, x);
  }
  
  inline SqrtTreeItem query(int l, int r, int betweenOffs, int base) {
    if (l == r) {
      return v[l];
    }
    if (l + 1 == r) {
      return op(v[l], v[r]);
    }
    int layer = onLayer[clz[(l - base) ^ (r - base)]];
    int bSzLog = (layers[layer]+1) >> 1;
    int bCntLog = layers[layer] >> 1;
    int lBound = (((l - base) >> layers[layer]) << layers[layer]) + base;
    int lBlock = ((l - lBound) >> bSzLog) + 1;
    int rBlock = ((r - lBound) >> bSzLog) - 1;
    SqrtTreeItem ans = suf[layer][l];
    if (lBlock <= rBlock) {
      SqrtTreeItem add = (layer == 0) ? (
        query(n + lBlock, n + rBlock, (1 << lg) - n, n)
      ) : (
        between[layer-1][betweenOffs + lBound + (lBlock << bCntLog) + rBlock]
      );
      ans = op(ans, add);
    }
    ans = op(ans, pref[layer][r]);
    return ans;
  }
public:
  inline SqrtTreeItem query(int l, int r) {
    return query(l, r, 0, 0);
  }
  
  inline void update(int x, const SqrtTreeItem &item) {
    v[x] = item;
    update(0, 0, n, 0, x);
  }
  
  SqrtTree(const vector<SqrtTreeItem>& a)
    : n((int)a.size()), lg(log2Up(n)), v(a), clz(1 << lg), onLayer(lg+1) {
    clz[0] = 0;
    for (int i = 1; i < (int)clz.size(); i++) {
      clz[i] = clz[i >> 1] + 1;
    }
    int tlg = lg;
    while (tlg > 1) {
      onLayer[tlg] = (int)layers.size();
      layers.push_back(tlg);
      tlg = (tlg+1) >> 1;
    }
    for (int i = lg-1; i >= 0; i--) {
      onLayer[i] = max(onLayer[i], onLayer[i+1]);
    }
    int betweenLayers = max(0, (int)layers.size() - 1);
    int bSzLog = (lg+1) >> 1;
    int bSz = 1 << bSzLog;
    indexSz = (n + bSz - 1) >> bSzLog;
    v.resize(n + indexSz);
    pref.assign(layers.size(), vector<SqrtTreeItem>(n + indexSz));
    suf.assign(layers.size(), vector<SqrtTreeItem>(n + indexSz));
    between.assign(betweenLayers, vector<SqrtTreeItem>((1 << lg) + bSz));
    build(0, 0, n, 0);
  }
};
```

### Обновление отрезков

sqrt-дерево умеет делать массовые операции, к примеру, присваивание на отрезке. Запрос $\text{massUpdate}(x, l, r)$ значит $a_i = x\ \forall i \in [l; r]$.

Есть два подхода к этой задаче. Первый подход созраняет асимптотику $O(1)$ на запрос, но асимптотика массового обновления становится $O(\sqrt{n}\cdot\log\log n)$. Во вотором подходе асимптотика запроса ухудшается до $O(\log\log n)$, а асимптотика обновления --- $O(\sqrt n)$.

Будем обновлять отрезок лениво (как в дереве отрезков): пометим некоторые вершины как _ленивые_, то есть в них не учтены обновления и надо их протолкнуть. Но есть одно отличие: проталкивание выполняется _долго_, поэтому в запросах его выполнять не получится. На нулевом уровне проталкивание занимает $O(\sqrt{n})$ времени, так что не будем проталкивать вершины в запросах, а будем просто учитывать обновления, если вершина или ее предок _ленивы_.

#### Первый подход

В первом подходе только вершины на уровне 1 могут быть ленивыми (их длина $O(\sqrt{n})$). При проталкивании такой вершины, она обновляет все свое поддерево включая себя за $O(\sqrt{n}\cdot\log\log n)$. В таком случае $\text{massUpdate}$ выполняется так:

- Рассмотрим вершины на уровне 1 и их соответствующие блоки.
- Некоторые из них полностью лежат в $\text{massUpdate}$. Пометим их как ленивые за $O(\sqrt{n})$.
- Некоторые лежат частично. Таких блоков не более двух. Перестроим их за $O(\sqrt{n}\cdot\log\log n)$. Если они были ленивыми, учтём это.
- Обновим $\text{prefixOp}$ и $\text{suffixOp}$ для частично покрытых блоков за $O(\sqrt{n})$, поскольку таких блоков не более 2.
- Перестроим $\text{index}$ за $O(\sqrt{n}\cdot\log\log n)$.

Таким образом можно делать $\text{massUpdate}$ быстро. Но как отложенные операции влияют на ответ на запрос? Они влияют так:

- Если запрос полностью лежит в ленивом блоке, просто выполним запрос и применим отложенное. $O(1)$.
- Если запрос состоит из нескольких блоков, некоторые из которых ленивы, то учитывать ленивые операции надо только в неполных граничных блоках --- центральная часть вычисляется через $\text{index}$, в котором уже все учтено. $O(1)$.

Асимптотика запроса осталась $O(1)$.

#### Второй подход

Во втором подходе каждая вершина кроме корня может быть ленивой. Ленивыми могут быть и вершины в $\text{index}$. Так как при обработке запроса необходимо проверить ленивость всех предков, то сложность запроса станет $O(\log\log n)$.

Но $\text{massUpdate}$ становится быстрее и выглядит так:

- Некоторые блоки полностью покрыты $\text{massUpdate}$. Пометим их как ленивые за $O(\sqrt{n})$.
- Обновим $\text{prefixOp}$ и $\text{suffixOp} для частично покрытых блоков за $O(\sqrt{n})$, поскольку таких блоков не более 2.
- Обновим $\text{index}$ за $O(\sqrt{n})$ (используется такой же алгоритм обновления).
- Обновим массив $\text{between}$ для _неиндексированных_ поддеревьев.
- Перейдем в вершины, соответствующие частично покрытым блокам и выбовем рекурсивно $\text{massUpdate}$.

В рекурсивном вызове делается $\text{massUpdate}$ на префиксе или на суффиксе, то есть непокрытый блок только один. Мы посещаем одну вершину на 1 уровне и по 2 вершины на последующих. Асимптотика $O(\sqrt{n} + \sqrt{\sqrt{n}} + \cdots) = O(\sqrt{n})$. Этот подход похож на такой же в массовых операциях на деревьях отрезков.

И автор поста на кф, и автор перевода слишком ленивы (как вершины в sqrt-дереве), чтобы писать код для отложенных операций на sqrt-дереве. Если вдруг у вас есть хорошая и протестированная реализация, сделайте pull request и напишите автору блога на Codeforces.

## Заключение

sqrt-дерево по функциональности не уступает дереву отрезков, но оно быстрее отвечает на запросы. Его слабая сторона --- медленные обновления. Оно может быть полезно, если много запросов (около `1e7`), но запросов обновления немного.
