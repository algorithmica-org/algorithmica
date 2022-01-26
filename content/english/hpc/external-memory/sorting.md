---
title: External Sorting
weight: 4
---

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

This is quite fast. If we have 1GB of memory and 10GB of data, this essentially means that we need a little bit more than 3 times the effort than just reading the data to sort it. Interestingly enough, we can do better.

### K-way Mergesort

Half of a page ago we have learned that in the external memory model, we can merge $k$ arrays just as easily as two arrays — at the cost of reading them. Why don't we apply this fact here?

Let's sort each block of size $M$ in-memory just as we did before, but during each merge stage, we will split sorted blocks not just in pairs to be merged, but take as many blocks we can fit into our memory during a k-way merge. This way the height of the merge tree would be greatly reduced, while each layer would still be done in $O(\frac{N}{B})$ IOPS.

How many sorted arrays can we merge at once? Exactly $k = \frac{M}{B}$, since we need memory for one block for each array. Since the total amount of layers will be reduced to $\log_{\frac{M}{B}} \frac{N}{M}$, the whole complexity will be reduced to

$$
SORT(N) \stackrel{\text{def}}{=} O\left(\frac{N}{B} \log_{\frac{M}{B}} \frac{N}{M} \right)
$$

Note that, in our example, we have 10GB of data, 1GB of memory, and the block size is around 1MB for HDD. This makes $\frac{M}{B} = 1000$ and $\frac{N}{M} = 10$, and so the logarithm is less than one (namely, $\log_{1000} 10 = \frac{1}{3}$). Of course, we can't sort an array faster than reading it, so this analysis applies to the cases when we have very large dataset, small memory, and/or large block sizes, which happens in real life nowadays.

### Practical Implementation

Under more realistic constraints, instead of using $\log_{\frac{M}{B}} \frac{N}{M}$ layers, we can do just two: one for sorting data in blocks of $M$, and another one for merging all of them at once. With a gigabyte of RAM and a block size of 1MB, this would be enough to sort arrays up to a terabyte in size.

This way we would essentially just loop around our dataset twice. THe bandwidth of HDDs can be quite high, and we wouldn't want to stall it, so we need a slightly faster way to merge $k$ arrays than by finding minimum with $O(k)$ comparisons — namely, we can maintain for $k$ elements, and extract minimum elements from it in a manner almost identical to heapsort.

Here is the first phase looks in C++:

```cpp
const int B = (1<<20) / 4; // 1 MB blocks of integers
const int M = (1<<28) / 4; // available memory

FILE *input = fopen("input.bin", "rb");
std::vector<FILE*> parts;

while (true) {
    static int part[M]; // better delete it right after
    int n = fread(part, 4, M, input);

    if (n == 0)
        break;
    
    // sort in-memory
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
```

This would create many arrays named `part-000.bin`, `part-001.bin`, `part-002.bin` and so on.

What is left now is to merge them together. First we create the an array for storing pointers to current elements of all block, their separate buffers, and a priority queue, that we populate with their first elements:

```cpp
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
```

Now we need to populate the result file until it is full, carefully writing it and reading new batches of elements when needed:

```cpp
FILE *output = fopen("output.bin", "w");
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
```

This implementation is not particularly effective or safe-looking (well, this is basically C), but is a good educational example of how to work with low-level memory APIs.

## Joining

Sorting by mainly used not by itself, but as an intermediate step for other operations. One important real-world use case for external sorting is joining (as in "SQL join"), used in databases and other data processing applications.

**Problem.** Given two lists of tuples $(x_i, a_{x_i})$ and $(y_i, b_{y_i})$, output a list $(k, a_{x_k}, b_{y_k})$ such that $x_k = y_k$

The optimal solution would be to sort the two lists and then use the standard two-pointer technique to merge them. The I/O complexity here would be the same as sorting, and just $O(\frac{N}{B})$ if the arrays are already sorted.

This is why most data processing applications (databases, MapReduce systems) like to keep their tables at least partially sorted.

### Other Implementations

Note that this analysis is only applicable in external memory setting — that is, if you don't have the memory to fit entire dataset. In the real world, it is important to consider alternative methods.

The simplest of them is probably *hash join*, which goes something like this:

```python
def join(a, b):
    d = dict(a)
    for x, y in b:
        if x in d:
            yield d[x]
```

In external memory, joining two lists with a hash table would be unfeasible, as it would involve doing $O(M)$ entire block reads.

Another way is to use alternative sorting algorithms such as radix sort. In particular, radix sort would work in $O(\frac{N}{B} \cdot w)$ if enough memory is available to maintain a buffer possible key, which could be beneficial in the case of small keys and large datasets
