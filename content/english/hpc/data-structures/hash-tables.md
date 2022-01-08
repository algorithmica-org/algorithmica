---
title: Hash Tables
weight: 8
draft: true
---


## Hash Tables

![](https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Hash_table_3_1_1_0_1_0_0_SP.svg/2560px-Hash_table_3_1_1_0_1_0_0_SP.svg.png =500x)

----

### Chaining

![](https://upload.wikimedia.org/wikipedia/commons/d/d0/Hash_table_5_0_1_1_1_1_1_LL.svg =500x)

A lot of linked lists or growable arrays

----

### Open Addressing

![](https://upload.wikimedia.org/wikipedia/commons/b/bf/Hash_table_5_0_1_1_1_1_0_SP.svg =500x)

Fixed number of cells and a hash function $f_i(x)$ that decides where to look on $i$-th step

----

Implementation with a cyclic array:

```cpp
struct hashmap {
    const int size = (1<<24);
    int a[size] = {-1}, b[size];

    static inline int h(int x) { return (x^179)*7; }

    void add(int x, int y) {
        int k = h(x) % size;
        while (a[k] != -1 && a[k] != x)
            k = (k + 1) % size;
        a[k] = x, b[k] = y; 
    }

    int get(int x) {
        for (int k = h(x) % size; a[k] != -1; k = (k + 1) % size)
            if (a[k] == x)
                return b[k];
        return -1;
    }
};
```

Same asymptotic complexity, but 2-3x difference in real speed

----

![](https://upload.wikimedia.org/wikipedia/commons/1/1c/Hash_table_average_insertion_time.png =500x)

The only downside is that you need to rehash it more often
