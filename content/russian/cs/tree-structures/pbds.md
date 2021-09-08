---
title: Библиотека GNU C++ PBDS
draft: true
---

Для следующей структуры требуются следующие библиотеки

``` C++
#include <ext/pb_ds/assoc_container.hpp> // Общий файл.
#include <ext/pb_ds/tree_policy.hpp> // Содержит класс tree_order_statistics_node_update
```

и

``` C++
using namespace __gnu_pbds;
```

Иногда возникает желание, не просто делать то что умеет сет, но еще и
например запрос сколько чисел меньше нашего, с этим нам может помочь
`tree`

Шаблон `tree` имеет следующий вид:

``` C++
template<
typename Key, // Тип ключа
typename Mapped, // Тип ассоциированных с ключём данных
typename Cmp_Fn = std::less<Key>, // Функтор сравнения, должен соответствовать оператору <
typename Tag = rb_tree_tag, // Метка, обозначающая тип дерева
template<
typename Const_Node_Iterator,
typename Node_Iterator,
typename Cmp_Fn_,
typename Allocator_>
class Node_Update = null_node_update, // Метка обновления вершин
typename Allocator = std::allocator<char> > // Аллокатор
class tree;
```

`Tag` и `Node_Update` в обычном `map`'e отсутствуют.

`Tag` — класс, обозначающий структуру дерева. Есть три класса :
`rb_tree_tag`, `splay_tree_tag` и `ov_tree_tag`. Пока вам не нужно знать
что это, вам хватит только того, что вам нужно `rb_tree_tag`.
`Node_Update` — класс, обозначающий, что у нас поддерживается в
вершинах. Изначально - `null_node_update`, класс, который ничего
не хранит. Но в C++ есть `tree_order_statistics_node_update`, которая
хранит порядковую статистику.

``` C++
typedef tree<
int,
null_type,
less<int>,
rb_tree_tag,
tree_order_statistics_node_update>
ordered_set;
```

У этого контейнера, есть все, что есть у сета, кроме этого появляются
`find_by_order()` и `order_of_key()`. Первая возвращает итератор на
$k$-ый по величине элемент , вторая — дает количество элементов в
множестве, строго меньших, чем наш элемент.