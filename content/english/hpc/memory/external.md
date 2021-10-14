---
title: External Memory Model
weight: 1
draft: true
---

To reason about performance of memory-bound algorithms, we need to develop a cost model that is more sensitive to expensive block IO operations, but is not too rigorous to still be useful.

In the standard RAM model, we ignore the fact that primitive operations take unequal time to complete. Most importantly, it does not differentiate between operations on different types of memory, equating a read from RAM taking ~50ns in real-time with a read from HDD taking ~5ms, or about a $10^5$ times as much.

Similar in spirit, in *external memory model*, we simply ignore every operation that is not an I/O operation. More specifically, we consider one level of cache hierarchy and assume the following about the hardware and the problem:

- The size of the dataset is $N$, and it is all stored in *external* memory, which we can read and write in blocks of $B$ elements in a unit time (reading a whole block and just one element takes the same time).
- We can store $M$ elements in *internal* memory, meaning that we can store up to $\left \lfloor \frac{M}{B} \right \rfloor$ blocks.
- We only care about I/O operations: any computations done in-between reads and writes are free.
- We additionally assume $N \gg M \gg B$.

In this model, we measure performance of the algorithm in terms of its high-level *I/O operations*, or *IOPS* — that is, the total number of blocks read or written to external memory during execution.

We will mostly focus on the case where the internal memory is RAM and external memory is SSD or HDD, although the underlying analysis techniques that we will develop are applicable to any layer in the cache hierarchy. Under these settings, reasonable block size $B$ is about 1MB, internal memory size $M$ is usually a few gigabytes, and $N$ is up to a few terabytes.

## Array Scan

<!-- The external memory model can be used very efficiently without sacrificing simplicity. -->

As a simple example, when we calculate the sum of array by iterating through it one element at a time, we implicitly load it by chunks of $O(B)$ elements and, in terms of external memory model, process these chunks one by one:

$$
\underbrace{a_1, a_2, a_3,} _ {B_1}
\underbrace{a_4, a_5, a_6,} _ {B_2}
\ldots
\underbrace{a_{n-3}, a_{n-2}, a_{n-1}} _ {B_{m-1}}
$$

Thus, in external memory model, the complexity of summation and other linear array scans is

$$
SCAN(N) \stackrel{\text{def}}{=} O\left(\left \lceil \frac{N}{B} \right \rceil \right) \; \text{IOPS}
$$

Note that, in most cases, operating systems do this automatically. Even when the data is just redirected to the standard input from a normal file, the operating system buffers its stream and reads it in blocks of ~4KB (by default).

Now, let's slowly build up more complex things. The goal of this article is to eventually get to *external sorting* and its interesting applications. It will be based on the standard merge sort, so we need to derive a few of its primitives first.

## Merge

**Problem:** given two sorted arrays $a$ and $b$ of lengths $N$ and $M$, produce a single sorted array $c$ of length $N + M$ containing all of their elements.

The standard technique using two pointers looks like this:

```cpp
void merge(int *a, int *b, int *c, int n, int m) {
    int i = 0, j = 0;
    for (int k = 0; k < n + m; k++) {
        if (i < n && (j == m || a[i] < b[j]))
            c[k] = a[i++];
        else
            c[k] = b[j++];
    }
}
```

In terms of memory operations, we just linearly read all elements of $a$ and $b$ and linearly write all elements of $c$. Since these reads and writes can be buffered, it works in $SCAN(N+M)$ I/O operations.

So far the examples have been simple, and their analysis doesn't differ too much from the RAM model, except that we divide the final answer by the block size $B$. But here is a case where this is not so.

**K-way merging.** Consider the modification of this algorithm where we need to merge not just two arrays, but $k$ arrays of total size $N$ — by likewise looking at $k$ values, choosing the minimum between them, writing it into $c$ and incrementing one of the iterators.

In the standard RAM model, the asymptotic complexity would be multiplied $k$, since we would need to do $O(k)$ comparisons to fill each next element. But in external memory model, since everything we do in-memory doesn't cost us anything, its asymptotic complexity would not change as long as we can fit $(k+1)$ full blocks in memory, that is, if $k = O(\frac{M}{B})$.

Remember the $M \gg B$ assumption? If we have $M \geq B^{1+ε}$ for $\epsilon > 0$, then we can fit any sub-polynomial amount of blocks in memory, certainly including $O(\frac{M}{B})$. This condition is called *tall cache assumption*, and it is usually required in many other external memory algorithms.

## Merge Sorting

The "normal" complexity the standard mergesort algorithm is $O(N \log_2 N)$: on each of its $O(\log_2 N)$ "layers", the algorithms need to go through all $N$ elements in total and merge them in linear time.

In external memory model, when we read a block of size $M$, we can sort its elements "for free", since they are already in memory. This way we can split the arrays into $O(\frac{N}{M})$ blocks of consecutive elements and sort them separately as the base step, and only then merge them.

![](../img/k-way.png)

This effectively means that, in terms of IO operations, the first $O(\log M)$ layers of mergesort are free, and there are only $O(\log_2 \frac{N}{B})$ non-zero-cost layers, each mergeable in $O(\frac{N}{B})$ IOPS in total. This brings total I/O complexity to

$$
O(\frac{N}{B} \log_2 \frac{N}{M})
$$

Interestingly enough, we can do better.

### K-way Mergesort

Half of a page ago we have learned that in external memory model, we can merge $k$ arrays just as easily as two arrays — at the cost of reading them. Why don't we apply this fact here?

Let's, and then on each stage, we will not merge just two of them, but as many as we can fit in our memory — each layer would still work at the cost of reading the whole dataset

Instead of merging two arrays on 


Let's use this fact to merge as many arrays as possible at each step instead of just $2$. This would make the number of steps as low as possible.

How many can we merge? Exactly $k = \frac{M}{B}$, the upper bound on our memory. This will reduce the required amount of steps to $\log_{\frac{M}{B}} \frac{N}{B}$ and the whole complexity to $SORT(N) \stackrel{\text{def}}{=} O(\frac{N}{B} \log_{\frac{M}{B}} \frac{N}{B})$, since each layer still takes $O(\frac{M}{B})$ time to merge.

```cpp
#include <bits/stdc++.h>

const int B = (1<<20) / 4; // 1 MB blocks of integers
const int M = (1<<28) / 4; // available memory

const char* finput = "input.bin";
const char* foutput = "output.bin";

int main() {
    FILE *input = fopen(finput, "rb");

    std::vector<FILE*> parts;

    while (true) {
        static int part[M]; // better delete it right after
        int n = fread(part, 4, M, input);

        if (n == 0)
            break;
        
        std::sort(part, part + n);
        
        char fpart[sizeof "part-999.bin"];
        sprintf(fpart, "part-%03d.bin", parts.size());

        printf("Writing %d elements into %s...\n", n, fpart);

        FILE *file = fopen(fpart, "wb");
        fwrite(part, 4, n, file);
        fclose(file);
        
        file = fopen(fpart, "rb");
        parts.push_back(file);
    }

    fclose(input);

    std::priority_queue< std::pair<int, int> > q;

    const int nparts = parts.size();
    auto buffers = new int[nparts][B];
    int outbuffer[B];
    std::vector<int> l(nparts), r(nparts);

    for (int part = 0; part < nparts; part++) {
        r[part] = fread(buffers[part], 4, B, parts[part]);
        q.push({buffers[part][0], part});
        l[part] = 1;
    }

    FILE *output = fopen(foutput, "w");
    
    int buffered = 0;

    while (!q.empty()) {
        auto [key, part] = q.top();
        q.pop();

        outbuffer[buffered++] = key;
        if (buffered == B) {
            fwrite(outbuffer, 4, B, output);
            buffered = 0;
        }

        if (l[part] == r[part]) {
            r[part] = fread(buffers[part], 4, B, parts[part]);
            l[part] = 0;
        }

        if (l[part] < r[part]) {
            q.push({buffers[part][l[part]], part});
            l[part]++;
        }
    }

    fwrite(outbuffer, 4, buffered, output);

    delete[] buffers;
    for (FILE *file : parts)
        fclose(file);
    
    fclose(output);

    return 0;
}
```

## Join

In this article, we will discuss sorting in external memory and its one very important application: joining (like in "SQL Join" used in databases).

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

A list ranking algorithm may seem like something useless, but bear with me. In fact, this is a very important primitive that can be used particularly for many graph algorithms, as well as in parallel algorithms later.

### Algorithm

We can convert the initial problem to a slightly more general one. Assume that each element has a weight $w_i$ now and we need to compute sum of weights of all preceding elements instead of just rank. To solve the initial problem, we can set all weights equal to $1$.

The key idea is to remove some part of elements, recursively solve the problem, and then use it to reconstruct the answer for initial problem.

Consider three consecutive elements: $x$, $y$ and $z$. Assume we deleted $y$ and solved the problem for the remaining list, which included $x$ and $z$. Then we need to modify weights this way:
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

List ranking is very useful in graph algorithms.

For example, one can construct an euler tour of a tree by constructing a linked list where for each edge we add two copies of it, one for each direction. Then you can apply list ranking and get each node position.

Exactly same thing may be applied to parallel algorithms, but we will cover that more deeply later.

---

As you can see, joining—and, more fundamentally, sorting—is a very useful primitive for external memory algorithms.
