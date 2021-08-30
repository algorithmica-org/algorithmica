---
title: Многочлены
weight: 3
---

Обратим внимание на то, что любое число можно представить многочленом:

$$
\begin{aligned}
A(x) &= a_0 + a_1\cdot x + a_2 \cdot x^2  + \dots + a_n \cdot x^n
\\   &= a_0 + a_1\cdot 2 + a_2 \cdot 2^2 + \dots + a_n \cdot 2^n
\end{aligned}
$$

Основание x при этом может быть выбрано произвольно.

Чтобы перемножить два числа, мы можем перемножить соответствующие им многочлены, а затем произвести каррирование: пройтись от нижних разрядов получившегося многочлена и «сдвинуть» переполнившиеся разряды:

```cpp
const int base = 10;

vector<int> normalize(vector<int> a) {
    int carry = 0;
    for (int &x : a) {
        x += carry;
        carry = x / base;
        x %= base;
    }
    while (carry > 0) {
        a.push_back(carry % base);
        carry /= base;
    }
    return a;
}

vector<int> multiply(vector<int> a, vector<int> b) {
    return normalize(poly_multiply(a, b));
}
```

Прямая формула для произведения многочленов имеет вид

$$
\left(\sum_{i=0}^n a_i x^i\right)\cdot\left(\sum_{j=0}^m b_j x^j\right)=\sum_{k=0}^{n+m}x^k\sum_{i+j=k}a_i b_j
$$

Её подсчёт требует $O(n^2)$ операций, что нас не устраивает. Подойдём к этой задаче с другой стороны.
