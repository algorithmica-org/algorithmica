---
title: Segment Trees
weight: 3
draft: true
---

The lessons we learned from [optimizing](../s-tree) [binary search](../binary-search) can be applied to a broad range of data structures.

In this article, instead of trying to optimize something from the STL again, we will focus on *segment trees*, the structures that may be unfamiliar to most *normal* programmers and perhaps even most computer science researchers[^tcs], but are used [very extensively](https://www.google.com/search?q=segment+tree+site%3Acodeforces.com&newwindow=1&sxsrf=APq-WBuTupSOnSn9JNEHhaqtmv0Uq0eogQ%3A1645969931499&ei=C4IbYrb2HYibrgS9t6qgDQ&ved=0ahUKEwj2p8_og6D2AhWIjYsKHb2bCtQQ4dUDCA4&uact=5&oq=segment+tree+site%3Acodeforces.com&gs_lcp=Cgdnd3Mtd2l6EAM6BwgAEEcQsAM6BwgAELADEEM6BAgjECc6BAgAEEM6BQgAEIAEOgYIABAWEB46BQghEKABSgQIQRgASgQIRhgAUMkFWLUjYOgkaANwAXgAgAHzAYgB9A-SAQYxNS41LjGYAQCgAQHIAQrAAQE&sclient=gws-wiz) in programming competitions for their speed and simplicity of implementation.

[^tcs]: Segment trees are rarely mentioned in the scientific literature because they are relatively novel (invented ~2000), mostly don't do anything that [any other binary tree](https://en.wikipedia.org/wiki/Tree_(data_structure)) can't do, and *asymptotically* aren't faster — although, in practice, they often win by a lot in terms of speed.

### Dynamic Prefix Sum

<!--

This is a long article, and to make it less long, we will mostly be focusing on its simplest application -->

Segment trees are cool and can do lots of different things, but in this article, we will focus on their simplest non-trivial application — *the dynamic prefix sum problem*:

```cpp
void add(int k, int x); // react to a[k] += x (zero-based indexing)
int sum(int k);         // return the sum of the first k elements (from 0 to k - 1)
```

As we now have to support two types of queries, our optimization problem becomes multi-dimensional, and the optimal solution depends on the distribution of queries. For example, if one type of the queries were extremely rare, we would only optimize for the other, which is relatively easy to do:

- If we only cared about the cost of *updating the array*, we would store it as it is and [calculate the sum](/hpc/simd/reduction) directly on each `sum` query.
- If we only cared about the cost of *prefix sum queries*, we would keep it ready and [re-calculate them entirely from scratch](/hpc/algorithms/prefix) on each update.

Both of these options perform $O(1)$ work on one query type but $O(n)$ work on the other. When the query frequencies are relatively close, we can trade off the performance on one type of query for performance on the other. Segment trees let you do exactly that, achieving the equilibrium of $O(\log n)$ for both queries.

### Segment Tree Structure

The main idea behind segment trees is this:

- calculate the sum of the entire array and write it down somewhere;
- split the array into two halves, calculate the sum on both halves, and also write them down somewhere;
- split these halves into halves, calculate the total of four sums on them, and also write them down;
- …and so on, until we recursively reach segments of length one.

These computed subsegment sums can be logically represented as a binary tree — which is what we call a *segment tree*:

![](../img/segtree-path.png)

Segment trees have some nice properties:

- If the underlying array has $n$ elements, the segment tree has exactly $(2n - 1)$ nodes — $n$ leaves and $(n - 1)$ internal nodes — because each internal node splits a segment in two, and you only need $(n - 1)$ of them to completely split the original $[0, n-1]$ range.
- The height of the tree is $\Theta(\log n)$: on each next level starting from the root, the number of nodes roughly doubles and the size of their segments roughly halves.
- Each segment can be split into $O(\log n)$ non-intersecting segments that correspond to the nodes of the segment tree: you need at most two from each layer.

When $n$ is not a perfect power of two, not all levels are filled entirely — the last layer may be incomplete — but the truthfulness of these properties remains unaffected. The first property allows us to use only $O(n)$ memory to store the tree, and the last two let us solve the problem in $O(\log n)$ time:

- The `add(k, x)` query can be handled by adding the value `x` to all nodes whose segments contain the element `k`, and we've already established that there are only $O(\log n)$ of them.
- The `sum(k)` query can be answered by finding all nodes that collectively compose the `[0, k)` prefix and summing the values stored in them — and we've also established that there would be at most $O(\log n)$ of them.

But this is still theory. As we'll see later, there are remarkably many ways one can implement this data structure.

<!--

Note that by the same logic that each prefix can be covered by $O(\log n)$ nodes, each possible segment can also be covered by $O(\log n)$ nodes: you just possibly need at most two of them on each level. This lets us compute sums on any segment, although in this article we are not going to do it, instead reducing it to computing two prefix sums (from the right border, and the subtracting the prefix sum on the left border).

This is a general idea. Many different implementations possible, which we will explore one by one in this article.

Segment trees are built recursively: build a tree for left and right halves and merge results to get root.

Depending on the relative frequencies of the query types, the optimal solution may differ.

One way to do this is through a trick commonly called *square root decomposition*: we split the array (of size $n$) into blocks of approximately $\sqrt n$ elements,

sqrt

Enable [hugepages](/hpc/cpu-cache/paging) system-wide and forget about it.

Most of examples in this section are about optimizing some algorithms that are either included in standard library or take under 10 lines of code to implement naively, but we will start off with a bit more obscure example.

There are many things segment trees can do. Persistent structures, computational geometry. But for most of this article, we will focus on the dynamic (as opposed to static) prefix sum problem.

Segment trees are used for windowing queries or range queries in general, either by themselves or as part of a larger algorithm.

Functional programming, e. g. for implementing persistent arrays and derived structures.

-->

### Pointer-Based Implementation

The most straightforward way to implement a segment tree is to store everything we need in a node explicitly: including the array segment boundaries, the sum, and the pointers to its children.

If we were at the "Introduction to OOP" class, we would implement a segment tree recursively like this:

```c++
struct segtree {
    int lb, rb;                         // the range this node is responsible for 
    int s = 0;                          // the sum of elements [lb, rb)
    segtree *l = nullptr, *r = nullptr; // pointers to its children

    segtree(int lb, int rb) : lb(lb), rb(rb) {
        if (lb + 1 < rb) { // if the node is not a leaf, create children
            int m = (lb + rb) / 2;
            l = new segtree(lb, m);
            r = new segtree(m, rb);
        }
    }

    void add(int k, int x) { /* react to a[k] += x */ }
    int sum(int k) { /* compute the sum of the first k elements */ }
};
```

If we needed to build it over an existing array, we would rewrite the body of the constructor like this:

```c++
if (lb + 1 == rb) {
    s = a[lb]; // the node is a leaf -- its sum is the element a[lb]
} else {
    int t = (lb + rb) / 2;
    l = new segtree(lb, t);
    r = new segtree(t, rb);
    s = l->s + r->s; // we can use the sums of children that we've just calculated
}
```

The construction time is of no significant interest to us, so to reduce the mental burden, we will just assume that the array is zero-initialized in all future implementations.

Now, to implement `add`, we need to descend down the tree until we reach a leaf node, adding the delta to the `s` fields:

```c++
void add(int k, int x) {
    s += x;
    if (l != nullptr) { // check whether it is a leaf node
        if (k < l->rb)
            l->add(k, x);
        else
            r->add(k, x);
    }
}
```

<!--

We can do largely the same with the prefix sum query, adding the sum stored in the left node each time we go right:

-->

To calculate the sum on a segment, we can check if the query covers the current segment fully or doesn't intersect with it at all — and return the result for this node right away. If neither is the case, we recursively pass the query to the children so that they figure it out themselves:

```c++
int sum(int lq, int rq) {
    if (rb <= lq && rb <= rq) // if we're fully inside the query, return the sum
        return s;
    if (rq <= lb || lq >= rb) // if we don't intersect with the query, return zero
        return 0;
    return l->sum(k) + r->sum(k);
}
```

This function visits a total of $O(\log n)$ nodes because it only spawns children when a segment only partially intersects with the query, and there are at most $O(\log n)$ of such segments.

For *prefix sums*, these checks can be simplified as the left border of the query is always zero:

```c++
int sum(int k) {
    if (rb <= k)
        return s;
    if (lb >= k)
        return 0;
    return l->sum(k) + r->sum(k);
}
```

Since we have two types of queries, we also got two graphs to look at:

![](../img/segtree-pointers.svg)

While this object-oriented implementation is quite good in terms of software engineering practices, there are several aspects that make it terrible in terms of performance:

- Both query implementations use [recursion](/hpc/architecture/functions) — although the `add` query can be tail-call optimized.
- Both query implementations use unpredictable [branching](/hpc/pipelining/branching), which stalls the CPU pipeline.
- The nodes store extra metadata. The structure takes $4+4+4+8+8=28$ bytes and gets padded to 32 bytes for [memory alignment](/hpc/cpu-cache/alignment) reasons, while only 4 bytes are really necessary to hold the integer sum.
- Most importantly, we are doing [pointer chasing](/hpc/cpu-cache/latency): we have to fetch the pointers to the children to descend into them, even though we can infer, ahead of time, which segments we'll need just from the query.

Pointer chasing outweighs all other issues by orders of magnitude — and to negate it, we need to get rid of pointers, turning the structure *implicit*.

### Implicit Segment Trees

To store our segment tree implicitly, we can also use the [Eytzinger layout](../binary-search#eytzinger-layout), storing the nodes in a large array, where for every non-leaf node $v$ corresponding to the range $[l, r)$, the node $2v$ is its left child and the node $(2v+1)$ is its right child, corresponding to the ranges $[l, \lfloor \frac{l+r}{2} \rfloor)$ and $[\lfloor \frac{l+r}{2} \rfloor, r)$ respectively.

![The memory layout of implicit segment tree with the same query path highlighted](../img/segtree-layout.png)

One little problem with this layout is that if $n$ is not a perfect power of two, we would need more array cells to store the tree — $4n$, to be exact. The tree structure hasn't change, and there are still exactly $(2n - 1)$ nodes in the tree — they are just not compactly packed on the last layer.

```c++
int t[4 * N];
```

To implement `add`, we similarly implement a recursive function that uses this index arithmetic instead of pointers. Since we also don't store the borders of the segment, we need to pass them as parameters. This makes the function a bit clumsy, as there are now five of them in total that you need to pass around:

```c++
void add(int k, int x, int v = 1, int l = 0, int r = N) {
    t[v] += x;
    if (l + 1 < r) {
        int m = (l + r) / 2;
        if (k < m)
            add(k, x, 2 * v, l, m);
        else
            add(k, x, 2 * v + 1, m, r);
    }
}
```

To implement the prefix sum query, we do largely the same:

```c++
int sum(int k, int v = 1, int l = 0, int r = N) {
    if (l >= k)
        return 0;
    if (r <= k)
        return t[v];
    int m = (l + r) / 2;
    return sum(k, 2 * v, l, m)
         + sum(k, 2 * v + 1, m, r);
}
```

Apart from using much less memory, the main advantage is that we can now make use of [memory parallelism](/hpc/cpu-cache/mlp) and fetch the nodes we need in parallel, considerably improving the running time for both queries:

![](../img/segtree-topdown.svg)

To improve further, we can manually optimize the index arithmetic and replace division by two with an explicit binary shift — as the compilers [aren't always able](/hpc/compilation/contracts/#arithmetic) to do themselves — and, more importantly, remove the recursion and make the implementation iterative.

Here is how a fully iterative `add` looks like:

```c++
void add(int k, int x) {
    int v = 1, l = 0, r = N;
    while (l + 1 < r) {
        t[v] += x;
        v <<= 1;
        int m = (l + r) >> 1;
        if (k < m)
            r = m;
        else
            l = m, v++;
    }
    t[v] += x;
}
```

This is slightly harder to do for the `sum` query as it has two recursive calls. The trick is to notice that when we make these calls, one of them is guaranteed to terminate immediately, so we can simply check this condition when descend:

```c++
int sum(int k) {
    int v = 1, l = 0, r = N, s = 0;
    while (true) {
        int m = (l + r) >> 1;
        v <<= 1;
        if (k >= m) {
            s += t[v++];
            if (k == m)
                break;
            l = m;
        } else {
            r = m;
        }
    }
    return s;
}
```

This doesn't improve the performance for the update query by a lot because it was tail-recursive, and the compiler already performed a similar optimization, but the running time on the prefix sum query roughly halved for all problem sizes:

![](../img/segtree-iterative.svg)

This implementation still has some problems: we are potentially using twice as much memory as necessary, have maintain and re-compute array bounds, and we still have costly branching. To get rid of these problems, we need to change the approach a little bit.

### Bottom-Up Implementation

Let's change the definition of the implicit segment tree. Instead of relying on the parent-to-child relationship, we first assign all the leaf nodes numbers from $n$ to $(2n - 1)$, and then define the parent of node $k$ to be equal to node $\lfloor \frac{k}{2} \rfloor$. It's easy to see that you can still reach the root (node $1$) by dividing the node number by two, and each node still has at most two children — $2k$ and $(2k + 1)$ — as anything else would floor to another number.

```c++
int t[2 * N];
```

When $n$ is a power of two, this yields the same structure, and taking advantage of this bottom-up approach lets us starting from the leaf node and go up to the root:

```c++
void add(int k, int x) {
    k += N;
    while (k != 0) {
        t[k] += x;
        k >>= 1;
    }
}
```

To fix this, we can similarly calculate the sum of a segment in general. For that, we need to maintain two pointers on the first and the last node to be summed, and stop when they are giving an empty segment:

```c++
int sum(int l, int r) {
    l += N;
    r += N - 1;
    int s = 0;
    while (l <= r) {
        if ( l & 1) s += t[l++];
        if (~r & 1) s += t[r--];
        l >>= 1, r >>= 1;
    }
    return s;
}
```

This results and a much simpler and faster code. However, when the array size is not a power of two, the `sum` query doesn't work correctly. To understand why, consider at the tree structure for 13 elements:

![](../img/segtree-permuted.png)

The first index of the last layer is always a power of two, but when $n$ is not a power of two, some prefix of the leaf elements gets wrapped around to the right side of the tree.

Magically, it this works even for non-power-of-two array sizes and for queries where the left boundary is to the right of the right one because the left at some point will "wrap around", and when this happens, the `l <= r` condition will become false.

![](../img/segtree-bottomup.svg)

Now, since we are only interested in the prefix sum, and we'd want to get rid of maintaining `l` and only move the right border like this:

```c++
int sum(int k) {
    int res = 0;
    k += N - 1;
    while (k != 0) {
        if (~k & 1)
            res += t[k--];
        k = k >> 1;
    }
    return res;
}
```

It works when $n$ is a power of two, but fails for all other array sizes. To make it work for arbitrary array sizes, we can do the following trick: just permute the leaves so that they go in the right order, even though they span two layers. This can be done like this:

```c++
const int last_layer = 1 << __lg(2 * N - 1);

int leaf(int k) {
    k += last_layer;
    k -= (k >= 2 * N) * N;
    return k;
}
```

Now, when implementing the queries, all we need to do is to call the `leaf` function:

```c++
void add(int k, int x) {
    k = leaf(k);
    while (k != 0) {
        t[k] += x;
        k >>= 1;
    }
}

int sum(int k) {
    k = leaf(k - 1);
    int s = 0;
    while (k != 0) {
        if (~k & 1)
            s += t[k--];
        k >>= 1;
    }
    return s;
}
```

The last touch: by replacing the `s += t[k--]` line with predication, we can now make the implementation branchless (except for the last branch, where we check the loop condition):

```c++
int sum(int k) {
    k = leaf(k - 1);
    int s = 0;
    while (k != 0) {
        s += (~k & 1) ? t[k] : 0;
        k = (k - 1) >> 1;
    }
    return s;
}
```

Combined, these optimizations make the prefix sum queries run much faster:

![](../img/segtree-branchless.svg)

Notice that the bump in latency for the prefix sum query starts at $2^{19}$ and not at $2^{20}$, where we run out of the L3 cache. This is because we are still storing $2n$ integers, and also fetching the `t[k]` element regardless of whether we will add it to `s` or not. We can actually solve both of these problems.

### Fenwick trees

Implicit structures are great. They allow us to avoid pointer chasing and visit all the nodes relevant for a query in parallel. What is even better is *succinct* structures. In addition to not storing pointers or any other metadata, they also use the theoretically minimal memory to store the structure — maybe only with $O(1)$ more fields.

To make a segment tree succinct, we need to look at the values stored in the nodes and search for redundancies — the values that can be inferred from other nodes — and remove them. For any node $p$, its sum $s_p$ equals to the sum $(s_l + s_r)$ stored in its children nodes. Therefore, for any such "triangle" of nodes, we only need to store any two of $s_p$, $s_l$, or $s_r$, and we can restore the other one from the $s_p = s_l + s_r$ identity.

Note that in every implementation so far, we never added the sum stored in the right child when computing the prefix sum. *Fenwick tree* is a type of a segment tree that uses this consideration and gets rid of all *right* children, including the last layer. This makes the total required number of memory cells $n + O(1)$, the same as the underlying array.

![](../img/segtree-succinct.png)

To calculate a prefix sum, we need to repeatedly jump to the first parent that is a left child:

![A path for the sum query](../img/fenwick-sum.png)

To process an update query, we need to repeatedly add the delta to the first parent the contains the cell $k$:

![A path for the update query](../img/fenwick-update.png)

More formally, a Fenwick tree is defined as the array $t_i = \sum_{k=f(i)}^i a_k$ where $f$ is some function for which $f(i) \leq i$. If $f$ is the "remove last bit" function (`x -= x & -x`), then both query and update would only require updating $O(\log n)$ different $t$'s

```c++
int t[N + 1];
```

Now, instead of making it actually equivalent to a segment tree, we will make all sizes a power of two and maintain a *forest* of trees. In a sense, we maintain $O(\log n)$ different trees.

Now, the tricky part is how to do it *fast*. If the array size is a perfect power of two, we have a trick. Notice that what left children have in common is that their indices are even. If a node is a deep interior node, it will end with a lot of zeros in its binary representation. We can there just remove the last sequence of ones, which can be done with `k &= k - 1`:

```c++
int sum(int k) {
    int res = 0;
    for (; k != 0; k &= k - 1)
        res += t[k];
    return res;
}
```

Now, when we defined $f$, on update, we need to identify the nodes that contain the element that is being updated. Since the $f$ function removes the last index, these have to be the nodes that have the same number of zeros at the end, some of the same prefix, and some number of ones at the middle that will be cancelled to produce a number that is lower than the original one. All such numbers can be yielded by adding the last set bit to the index, which trims zeros:

```c++
void add(int k, int x) {
    for (k += 1; k <= N; k += k & -k)
        t[k] += x;
}
```

Sometimes people use `k -= k & -k` to iterate when processing the `sum` query, which makes this implementation delightfully symmetric.

This is a structure where it is easier to calculate sum on subsegments as the difference of two prefix sums:

```c++
// [l, r)
int sum (int l, int r) {
    return sum(r) - sum(l - 1);
}
```

The performance of the Fenwick tree is similar to the optimized bottom-up segment tree:

![](../img/segtree-fenwick.svg)

There is, however, one weird thing. The performance goes up rapidly close to the L3 boundary. This is a [cache associativity](/hpc/cpu-cache/associativity) effect: the most frequently used cells all have their index divisible by large powers of two and get aliased to the same cache set, kicking each other out.

One way to negate this is to insert "holes" in the layout like this:

```c++
inline constexpr int hole(int k) {
    return k + (k >> 10);
}

int t[hole(N) + 1];

void add(int k, int x) {
    for (k += 1; k <= N; k += k & -k)
        t[hole(k)] += x;
}

int sum(int k) {
    int res = 0;
    for (; k != 0; k &= k - 1)
        res += t[hole(k)];
    return res;
}
```

As computing the `hole` function is not on the critical path between iteration, it does not introduce any significant overhead, but completely removes the cache associativity problem and shrinks the latency by ~3x on large arrays:

![](../img/segtree-fenwick-holes.svg)

There are still other minor issues with Fenwick trees. Similar to [binary search](../binary-search), the temporal locality of its memory accesses is not great, as rarely accessed elements are grouped with the most frequently accessed ones. It also executes has to perform end-of-loop checks and executes non-constant number of iterations, likely causing a branch mispredict, although just a single one.

But we are going to leave it there and focus on an entirely different approach. If you know [S-trees](../s-tree), you've probably guessed where this is going.

### Wide Segment Trees

Here is the idea: if we are fetching a full cache line anyway, let's fill it with information that lets us process the query quicker. So let's store more than one data point in a segment tree node — this lets us reduce the tree height and do less iterations descending it.

![](../img/segtree-wide.png)

We can use a similar constexpr-based approach we used in [S+ trees](../s-tree#implicit-b-tree-1) to implement it:

```c++
const int b = 4, B = (1 << b);

constexpr int height(int n) {
    return (n <= B ? 1 : height(n / B) + 1);
}

constexpr int offset(int h) {
    int s = 0, n = N;
    while (h--) {
        s += (n + B - 1) / B * B;
        n /= B;
    }
    return s;
}

constexpr int H = height(N);
alignas(64) int t[offset(H)];
```

We effectively reduce the height of the tree by $\frac{\log_B n}{\log_2 n} = \log_2 B$ times, but it may be tricky to realize in-node operations.

In this context, we have to options:

1. We could store $B$ sums in each node.
2. We could store $B$ prefix sums in each node.

If we go with option 1, the `add` query would be largely the same, but the `sum` query would need to sum up to $B$ scalar in each node. If we go with option 2, the `sum` query would be trivial, but the `add` query will need to add the element to some suffix of each node.

In either case, one operation will perform $O(\log_B n)$ operations and rouch one scalar, while the other will perform $O(B \cdot \log_B n)$ operations. However, we really want to use [SIMD](/hpc/simd) to accelerate the slower operation. Since there are no fast [horizontal reductions](/hpc/simd/reduction), but it is easy to add a vector to a vector, we will stick to the second approach and store prefix sums in each node.

This makes the `sum` query very easy:

```c++
int sum(int k) {
    int res = 0;
    for (int h = 0; h < H; h++)
        res += t[offset(h) + (k >> (h * b))];
    return res;
}
```

For the `add` query, however, we need a trick. We only need to add a number to a prefix of a node. We need a mask that will tell us which element to add and which not. We can pre-calculate such a $B \times B$ mask just once, which tells us for each starting position whether the element is engaged in the operation or not:

```c++
struct Precalc {
    alignas(64) int mask[B][B];

    constexpr Precalc() : mask{} {
        for (int k = 0; k < B; k++)
            for (int i = 0; i < B; i++)
                mask[k][i] = (i > k ? -1 : 0);
    }
};

constexpr Precalc T;
```

We then use these masks to bitwise-and the broadcasted delta value and add it to the values stored at the node:

```c++
typedef int vec __attribute__ (( vector_size(32) ));

constexpr int round(int k) {
    return k & ~(B - 1); // = k / B * B
}

void add(int k, int x) {
    vec v = x + vec{};
    for (int h = 0; h < H; h++) {
        auto a = (vec*) &t[offset(h) + round(k)];
        auto m = (vec*) T.mask[k % B];
        for (int i = 0; i < B / 8; i++)
            a[i] += v & m[i];
        k >>= b;
    }
}
```

This speeds up the `sum` query by more than 10x and the `add` query by up to 4x compared to the Fenwick tree:

![](../img/segtree-simd.svg)

Wide Fenwick trees make little sense. The speed of Fenwick trees comes from rapidly iterating over just the elements we need.

Unlike [S-trees](../s-tree), you can easily change block size:

![](../img/segtree-simd-others.svg)

Expectedly, when we increase the node size, the update time also increases, as we need to fetch more cache lines and process them, but the `sum` query time decreases, as the size of the tree becomes smaller.

There are similar considerations to [S+ trees](../s-tree/#modifications-and-further-optimizations) in that the ideal layout (the node sizes on each layer) may depend on the use case.

### Comparison

This is significantly faster compared to the popular segment tree implementations:

![](../img/segtree-popular.svg)

It makes sense to look at the relative speedup:

![](../img/segtree-popular-relative.svg)

The wide segment tree is up to 200 and 40 times faster than the pointer-based segment tree for the prefix sum and update queries respectively, although for sufficiently large arrays, memory efficiency becomes the only concern, and this speedup goes down to 60 and 15 respectively.

### Modifications

We mostly focused on the prefix sum problem, but this general structure can be used for other problems handled by segment trees:

- General sums and other reductions.
- Range minimum sum queries.
- Fixed-universe heaps.

Some more exotic applications, reliant on there being pointers, are expectedly harder. To implement dynamic trees, we could store the mapping between the node number and the tree in a hash table. For more complicated cases, such as whether wide segment trees can help in implementing persistent trees is an open question.

why b-ary Fenwick tree is not a good idea

### Acknowledgements

This article is loosely based on "[Practical Trade-Offs for the Prefix-Sum Problem](https://arxiv.org/pdf/2006.14552.pdf)" by Giulio Ermanno Pibiri and Rossano Venturini. It has some more detailed discussions, as well as some other implementations or branchless top-down segment tree and why b-ary Fenwick tree is not a good idea. Intermediate structures we've skipped here.

Some code was borrowed from "[Efficient and easy segment trees](https://codeforces.com/blog/entry/18051)" by Oleksandr Bacherikov.
