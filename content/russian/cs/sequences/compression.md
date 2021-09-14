---
title: Сжатие координат
authors:
- Сергей Слотин
weight: -1
---


## Сжатие координат
Это общая идея, которая может оказаться полезной. Пусть, есть $n$ чисел $a_1,\ldots,a_n$. Хотим, преобразовать $a_i$ так, чтобы равные остались равными, разные остались разными, но все они были от 0 до $n-1$. Для этого надо отсортировать числа, удалить повторяющиеся и заменить каждое $a_i$ на его индекс в отсортированном массиве.


```
int a[n], all[n];
for (int i = 0; i < n; ++i) {
    cin >> a[i];
    all[i] = a[i];
}
sort(all, all + n);
m = unique(all, all + n) - all; // теперь m - число различных координат
for (int i = 0; i < n; ++i)
    a[i] = lower_bound(all, all + m, x[i]) - all;
```

```cpp
vector<int> compress(vector<int> a) {
    unordered_map<int, int> m;
    for (int x : a)
        if (m.count(x))
            m[x] = m.size();
    for (int &x : a)
        x = m[x];
    return a;
}
```


```cpp
vector<int> compress(vector<int> a) {
    vector<int> b = a;
    sort(b.begin(), b.end());
    b.erase(unique(b.begin(), b.end()), b.end());
    for (int &x : a)
        x = int(lower_bound(b.begin(), b.end(), x) - b.begin());
    return a;
}
```
