---
title: Оптимизация Кнута
---

Предыдущий метод опирался на тот факт, что $opt[i, j] \leq opt[i, j+1]$. Асимптотику можно ещё улучшить, если $opt$ монотонен ещё и по первому параметру:

$$
opt[i-1, j] \leq opt[i, j] \leq opt[i, j+1]
$$

В задаче это выполняется примерно по той же причине: если нам нужно покрывать меньше точек, то последний отрезок будет начинаться не позже старого.

Будем просто для каждого состояния перебирать элементы непосредственно от $opt[i-1, j]$ до $opt[i, j+1]$ — можно идти в порядке увеличения $i$ и уменьшения $j$, и тогда эти $opt$ уже будут посчитаны к нужному моменту. 

Выясняется, что это работает быстро. Чтобы понять, почему, распишем количество элементов, которые мы просмотрим для каждого состояния, и просуммируем:

$$
\sum_{i, j} (opt[i, j+1] - opt[i-1, j] + 1) = nm + \sum_{ij} (opt[i, j+1] - opt[i-1, j])
$$

Заметим, что все элементы, кроме граничных, учитываются в сумме ровно два раза — один раз с плюсом, другой с минусом — а значит их можно сократить.  Граничных же элементов $O(n)$ и каждый из них порядка $O(n)$. Значит, итоговая асимптотика составит $O(n \cdot m + n \cdot n) = O(n^2)$.

```c++
for (int i = 1; i <= n; i++) {
    for (int j = m; j >= 1; j--) {
        for (int k = opt[i-1][j]; k <= opt[i][j+1]; k++) {
            int val = f[i+1][k-1] + cost(i, j);
            if (val < f[t][k])
                f[t][k] = val, opt[i][j] = i;
        }
    }
}
```

Реализация получилась очень лаконичной: она всего на 3 строчки длиннее, чем базовое решение.
