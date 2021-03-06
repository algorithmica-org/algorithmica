---
title: Запросы на деревьях
---

Дерево называется *корневым*, если оно ориентированно, и из какой-то вершины (называемой *корнем*) можно попасть во все остальные.

Примеры корневых деревьев:

* наследование классов в языках программирования (если множественное наследование запрещено),
* дерево факторизации числа на простые (в общем случае не уникальное),
* иерархия в какой-нибудь организации,
* дерево парсинга математичеких выражений.

Задачи на корневые деревья весьма бесполезны в реальной жизни, но зато очень интересны с алгоритмической точки зрения, и поэтому часто встречаются на олимпиадах по программированию.

![](https://raw.githubusercontent.com/e-maxx-eng/e-maxx-eng/mastimg/LCA_Euler.png)

## Свойства dfs

Посчитаем для каждой вершины времена входа ($tin$) и выхода ($tout$) из неё во время эйлерова прохода:

```c++
vector<int> g[maxn];
int p[maxn], tin[maxn], tout[maxn];
int t = 0;

void dfs (int v) {
    tin[v] = t++;
    for (int u : g[v])
        dfs(u);
    tout[v] = t; // иногда счётчик тут тоже увеличивают
}
```

У этих массивов много полезных свойств:

* Вершина $u$ является предком $v$ $\iff tin_v \in [tin_u, tout_u)$. Эту проверку можно делать за константу.
* Два полуинтервала — $[tin_v, tout_v)$ и $[tin_u, tout_u)$ — либо не пересекаются, либо один вложен в другой.
* В массиве $tin$ есть все числа из промежутка от 0 до $n-1$, причём у каждой вершины свой номер.
* Размер поддерева вершины $v$ (включая саму вершину) равен $tout_v - tin_v$.
* Если ввести нумерацию вершин, соответствующую $tin$-ам, то индексы любого поддерева всегда будут каким-то промежутком в этой нумерации.

### Запросы на поддеревьях

Последнее свойство на самом деле очень важное. Его можно использовать для обработки разных запросов на поддеревьях, сводя их к запросам на подотрезках, которые уже можно решать стандартными методами — например, через [дерево отрезков](segtree).

Пример задачи:

> Есть корневое дерево. Рядом с каждой вершиной записано число. Поступают два типа запросов: прибавить ко всем вершинам на каком-то поддереве число $x_i$ и найти значение числа у вершины $v_i$.

Выпишем все числа у вершин в один массив, в позиции, соответствующие их $tin$-ам. Что такое «прибавить на поддереве» относительно этого массива? Это то же, самое, что прибавить какую-то константу на каком-то подотрезке, а это можно делать любой [достаточно продвинутой структурой](segtree).

### Запросы на уровнях

> Дано корневое дерево. Требуется отвечать на запросы нахождения $d_i$-того предка вершины $v_i$, то есть вершины-предка, находящейся на расстоянии $d_i$ от $v_i$.

Создадим $h$ векторов, где $h$ — высота дерева. Для каждой вершины, во время прохода в dfs, добавим её $tin$ в вектор, соответствующей её глубине. Получаем $h$ отсортированных векторов.

Теперь заметим, что внутри одного вектора все отрезки поддеревьев вершин — $[tin_v, tout_v)$ — тоже не пересекаются, а значит ещё и отсортированы. Тогда ответа на запрос мы можем просто взять $tin$ вершины-запроса, посмотреть на вектор нужного уровня и за $O(\log n)$ сделать бинпоиск по нужному отрезку.

Также существует другой способ, требующий $O(1)$ времени на запрос, но $O(n \log n)$ памяти на предпосчёт — [лестничная декомпозиция](https://neerc.ifmo.ru/wiki/index.php?title=Level_Ancestor_problem).

### Запросы на путях

Пусть нас вместо LCA спрашивают, например, о минимуме на произвольном пути (на всех рёбрах записаны какие-то числа).

Мы можем сделать такой же предподсчет, как в методе двоичных подъемов, но хранить вместе с номером $2^d$-ого предка минимум на соответствующем пути.

Заметим, что минимум на пути от $u$ до $v$ — это минимум от минимума на пути от $u$ до $lca(u, v)$ и от минимума на пути от $v$ до $lca(u, v)$. В свою очередь, оба этих минимума — это минимум на всех двоичных подъемах до LCA.

```c++
int get_min (int v, int u) {
    int res = inf;
    for (int l = logn-1; l >= 0; l--)
        if (!ancestor(up[v][l], u))
            v = up[v][l], res = min(res, mn[v][l]);
    for (int l = logn-1; l >= 0; l--)
        if (!ancestor(up[u][l], v))
            u = up[u][l], res = min(res, mn[u][l]);
    return min({res, mn[v][0], mn[u][0]})
}
```

Аналогичным образом можно считать сумму, `gcd`, полиномиальный хэш и много других странных функций на пути, но только в статическом случае (когда у нас нет обновлений). Для динамического случая существует весьма сложный метод, называемый [heavy-light декомпозицией](hld).
