Рассмотрим произвольное корневое дерево, и пару его вершин $u, v$.
Вершина $x$ называется $lca_{u, v}$, если $x\~-$ предок $v$,
$x\~-$ предок $u$, и $x$ является самой удаленной от корня вершиной
среди тех, которые удовлетворяли двум предыдущим условиям.

В чем польза от нахождения $lca$? К примеру, $lca_{v, u}$ разбивает
путь $v \\rightarrow u$ на два вертикальных непересекающихся, что
может очень облегчить работу в задачах с запросами на пути.

Есть две популярные техники для нахождения $lca$:

  - Двоичные подъемы
  - RMQ на эйлеровом обходе

### Двоичные подъемы

Для каждой вершины сохраним массив $parent_{v, k}$, в котором будет
храниться предок вершины $v$ на высоте $2^k$. Тогда $parent_{v, k}
= parent_{parent_{v, k - 1}, k - 1}$.

Зная массив $parent$, можно найти $lca$. Рассмотрим $a = parent_{v,
k}$. Если $a$ не предок $u$, то $lca(v, u) = lca(a, u)$. Таким образом,
с помощью спуска по степеням двойки можно найти самую высокую вершину
$a$, которая соответствует $lca(v, u) = lca(a, u)$. Но тогда ее предок и
будет $lca(v, u)$.

### RMQ на эйлеровом обходе

Выпишем [эйлеров обход дерева](Эйлеров_обход "wikilink") (выписывая
вершину каждый раз, как мы в нее попадаем). Заметим, что $lca(v,
u)$ это вершина с наименьшей высотой среди всех вершин от $v$ до $u$ в
эйлеровом обходе (потому что она точно там присутствует, а ее предка
там быть не может). С помощью [Sparse Table](Sparse_Table "wikilink")
будем искать минимум высот на отрезке (не забудем хранить номер
вершины, для восстановления отрезка)

[Категория:Конспекты](Категория:Конспекты "wikilink")