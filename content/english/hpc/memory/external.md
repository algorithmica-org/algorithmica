---
title: External Memory Model
weight: 1
draft: true
---

In this article, we will discuss sorting in external memory and its one very important application: joining (like in "SQL Join" used in databases).

The main algorithm will be based on standard merge sort, so we need to derive a few of its primitives first.

## Merge

**Probem:** given two sorted arrays $a$ and $b$ of lengths $N$ and $M$, produce a single sorted array $c$ that contains all of their elements.

The standard technique is to use two pointers like this:

```cpp
void merge(int a[], int b[], int c[], int n, int m) {
    int i = 0, j = 0;
    for (int k = 0; k < n + m; k++) {
        if (i < n && (j == m || a[i] < b[j]))
            c[k] = a[i++];
        else
            c[k] = b[j++];
    }
}
```

Since reads and writes can be bufferized, it works in $SCAN(N+M)$ I/O operations.

**K-way merging**. One important difference is that merging $k$ arrays works in linear time too as long as we can fit $(k+1)$ full blocks in memory, that is, if $k = O(\frac{M}{B})$.

Remember the $M \gg B$ assumption? If we have $M \geq B^{1+ε}$ for $\epsilon > 0$, then we can fit any sub-polynomial amount of blocks in memory. This is also called *tall cache assumption* and is required in many external memory algorithms.

## Merge Sorting

"Normal" complexity of a standard merge sort is $O(N \log_2 N)$: on each of $O(\log_2 N)$ "layers" it would in total need to go through all of $N$ elements. How well would it do in terms of I/O operations?

In external memory model, we can sort elements inside $N \over B$ consecutive blocks "for free" in-memory after reading them. This reduces the amount of real "layers" from $O(\log_2 N)$ to $O(\log_2 \frac{N}{B})$.

After that, each merge step is performed at the cost of scanning the whole layer. This brings total I/O complexity to $O(\frac{N}{B} \log_2 \frac{N}{B})$.

Can we do better?

![](../img/k-way.png)

## K-way Mergesort

We learned that, unlike in the RAM model, we can merge $k$ arrays at the cost of reading them. Let's use this fact to merge as many arrays as possible at each step instead of just $2$. This would make the number of steps as low as possible.

How many can we merge? Exactly $k = \frac{M}{B}$, the upper bound on our memory. This will reduce the required amount of steps to $\log_{\frac{M}{B}} \frac{N}{B}$ and the whole complexity to $SORT(N) \stackrel{\text{def}}{=} O(\frac{N}{B} \log_{\frac{M}{B}} \frac{N}{B})$, since each layer still takes $O(\frac{M}{B})$ time to merge.

## Join

Real-world application of sorting is joining. Consider the following problem: 

> Given two lists of tuples $(x_i, a_{x_i})$ and $(y_i, b_{y_i})$, output a list $(k, a_{x_k}, b_{y_k})$ such that $x_k = y_k$

The optimal solution would be to sort the two lists and use two-pointer technique to merge them. The I/O complexity here would be the same as sorting.

This is why data processing applications (databases, MapReduce systems) like to keep their tables sorted.

## If You Have the Memory

Notice that this all is only applicable in external memory settings, that is, if you don't have the memory to fit entire dataset.

In real world, it is important to consider trade offs between these methods.

### Hash Join

If you have the memory, this is how you join lists in linear time:

```python
def join(a, b):
    d = dict(a)
    for x, y in b:
        if x in d:
            yield d[x]
```

In external memory, joining two lists using a hash table is unfeasible, as it would involve doing $O(M)$ entire block reads.

### Non-Comparison Sorting

Radix sort: apply *stable* count sorting for each "radix"

```cpp
const int c = (1<<16);

void radix_sort(vector<int> &a) {
    vector<int> b[c];
    
    for (int x : a)
        b[x % c].push_back(x);
    
    for (int i = 0, k = 0; i < c; i++) {
        for (int x : b[i])
            a[k++] = x;
        b[i].clear();
    }
    
    for (int x : a)
        b[x / c].push_back(x);
    
    for (int i = 0, k = 0; i < c; i++)
        for (int x: b[i])
            a[k++] = x
}
```

$O(\frac{N}{B} \cdot w)$ if we have the memory

Could be beneficial in the case of small keys and large datasets

## List Ranking

The list ranking problem can be formulated like this: given a linked list, compute *rank* of each element, that is its distance from the front element.

The problem is easily solvable in RAM model, but an optimal solution in external memory it is nontrivial, because our data is store chaotically, and we can't simply traverse the list by querying each new element. 

![](../img/list-ranking.png)

A list ranking algorithm may seem like something useless, but bear with me. In fact, this is a very important primitive that can be used particularily for many graph algorithms, as well as in parallel algorithms later.

### Algorithm

We can convert the initial problem to a slightly more general one. Assume that each element has a weight $w_i$ now and we need to compute sum of weights of all preceding elements instead of just rank. To solve the initial problem, we can set all weights equal to $1$.

The key idea is to remove some part of elements, recursively solve the problem, and then use it to reconstruct the answer for initial problem.

Consider three consecutive elements: $x$, $y$ and $z$. Assume we deleted $y$ and solved the problem for the remainig list, which included $x$ and $z$. Then we need to modify weights this way:
- $w_y' = w_y + w_x$
- $w_z' = w_z + w_y$

On each step, we want to remove as many elements as possible, with a constraint that we can't really remove two consecutive elements because then merging results would be not that simple. Ideally we would want to split out list into even and odd elements, but doing this is not simpler than the initial problem.

One workaround is to choose the elements at random: toss a coin for each element, and then remove all "heads" after which a "tail" follows. You can see that no two consecutive elements are being selected, and on average we throw out ¼ of the dataset.

The arithmetic complexity would be linear, because $T(N) = T(\frac{3}{4} N) = O(N)$.

The only tricky part is how to implement the merge step in external memory. 

We maintain our list in the following form:
- List of tuples $(i, j)$ indicating that element $j$ follows after element $i$
- List of tuples $(i, w_i)$ indicating that element $i$ currently has weight $w_i$
- A list of deleted elements

Next we iterate over all lists using three pointers looking for deleted elements, and for each such element, we add write $(j, w_i)$ to a separate table, which would signify that before the recursive step we need to add $w_i$ to $j$. We can then join this new table with initial weights and perform the additions.

After coming back from recursion, we need to update weights for the deleted elements, which we can do with the same technique, but we need to iterate reversed connections instead of direct ones.

Asymptotic will be the same as joining, namely $SORT(N)$.

### Applications

List ranking is very usefull in graph algorithms.

For example, one can construct an euler tour of a tree by constructing a linked list where for each edge we add two copies of it, one for each direction. Then you can apply list ranking and get each node position.

Exactly same thing may be applied to parallel algorithms, but we will cover that more deeply later.

---

As you can see, joining—and, more fundamentally, sorting—is a very useful primitive for external memory algorithms.

---



To reason about memory and not go crazy, we need a model that is more sensitive, yet not so rigorous.

In RAM model, we ignored the fact that primitive operations take unequal time.

But consider an algoritm that does something on the memory. Each access takes at least 10ms.

In these cases, we can use a different cost model without sacrificing simplicity: we ignore all computation except for I/O operations.

A bit informal description:

Consider one level in cache hierarchy. 
- Data size is $N$, it is stored in *external* memory, which we can read and write in blocks of $B$ elements in one unit time (reading a whole block and just one element takes the same time).
- We can store $M$ elements *internal* memory, meaning that we can store $\left \lfloor \frac{M}{B} \right \rfloor$ blocks.
- We only care about I/O: any computation done in-between reads and writes is free.
- We assume $N \gg M \gg B$

It is measured in *I/O operations* or *IOPS*.

## Array Scan

For example, when we calculate $\sum_i a_i$ by iterating through array, it takes $SCAN(N) \stackrel{\text{def}}{=} O(\left \lceil \frac{N}{B} \right \rceil)$ IOPS.

$$
\underbrace{a_1, a_2, a_3,} _ {B_1}
\underbrace{a_4, a_5, a_6,} _ {B_2}
\ldots
\underbrace{a_{n-3}, a_{n-2}, a_{n-1}} _ {B_{m-1}}
$$

One thing you need to consider is buffering. By the way, this is what happens with console input and output.

```cpp
int scan() {
    // some explicit implementation
}
```

When you are just working on the RAM level, it happens by default. Same thing with mmap-ed files.
