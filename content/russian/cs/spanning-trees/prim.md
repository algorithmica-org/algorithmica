---
title: Алгоритм Прима
weight: 2
prerequisites:
  - safe-edge
published: true
---

Лемма о безопасном ребре говорит, что мы можем строить минимальный остов постепенно, добавляя по одному ребра, про которые мы точно знаем, что они минимальные для соединения какого-то разреза.

Один из подходов это использовать заключается в *алгоритме Прима*:

- Изначально остов — одна произвольная вершина.
- Пока минимальный остов не найден, выбирается ребро минимального веса, исходящее из какой-нибудь вершины текущего остова в вершину, которую мы ещё не добавили. Добавляем это ребро в остов и начинаем заново, пока остов не будет найден.

Этот алгоритм очень похож на алгоритм Дейкстры, только мы выбираем следующую вершину с другой весовой функцией — вес минимального соединяющего ребра вместо суммарного расстояния до неё.

Совсем наивная реализация за $O(nm)$ — каждый раз перебираем все рёбра:

```c++
const int maxn = 1e5, inf = 1e9;
vector from, to, weight;
bool used[maxn]

// считать все рёбра в массивы

used[0] = 1;
for (int i = 0; i < n-1; i++) {
    int opt_w = inf, opt_from, opt_to;
    for (int j = 0; j < m; j++)
        if (opt_w > weight[j] && used[from[j]] && !used[to[j]])
            opt_w = weight[j], opt_from = from[j], opt_to = to[j]
    used[opt_to] = 1;
    cout << opt_from << " " << opt_to << endl;
}
```

Реализация за $O(n^2)$:

```c++
const int maxn = 1e5, inf = 1e9;
bool used[maxn];
vector< pair<int, int> > g[maxn];
int min_edge[maxn] = {inf}, best_edge[maxn];
min_edge[0] = 0;

// ...

for (int i = 0; i < n; i++) {
    int v = -1;
    for (int u = 0; u < n; u++)
        if (!used[u] && (v == -1 || min_edge[u] < min_edge[v]))
            v = u;

    used[v] = 1;
    if (v != 0)
        cout << v << " " << best_edge[v] << endl;

    for (auto e : g[v]) {
        int u = e.first, w = e.second;
        if (w < min_edge[u]) {
            min_edge[u] = w;
            best_edge[u] = v;
        }
    }
}
```

Также, как в алгоритме Дейкстры, можно не делать линейный поиск оптимальной вершины, а поддерживать его в приоритетной очереди. Получается реализация за $O(m \log n)$:

```c++
set< pair<int, int> > q;
int d[maxn];

while (q.size()) {
    v = q.begin()->second;
    q.erase(q.begin());

    for (auto e : g[v]) {
        int u = e.first, w = e.second;
        if (w < d[u]) {
            q.erase({d[u], u});
            d[u] = w;
            q.insert({d[u], u});
        }
    }
}
```

Про алгоритм за $O(n^2)$ тоже забывать не стоит — он работает лучше в случае плотных графов.
