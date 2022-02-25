---
title: Segment Trees
weight: 3
draft: true
---

The lessons we learned from [optimizing](../binary-search) [binary search](../s-tree) can be applied to a broader range of data structures.

In this article, instead of trying to optimize something from the STL, we will focus on the *segment tree* — a structure that may be unfamiliar to most *normal* programmers and perhaps even most computer science researchers[^tcs], but is used very extensively in [programming competitions](https://codeforces.com/) for its speed and simplicity of implementation.

[^tcs]: Segment trees are rarely mentioned in scientific literature because they are relatively novel (invented around 2000), and *asymptotically* don't do anything that [any other binary tree](https://en.wikipedia.org/wiki/Tree_(data_structure)) can't do, but they are much faster *in practice* for the problems they solve.

This is a long article, and to make it less long, we will mostly be focusing on its simplest application

Segment trees are cool and can do lots of different things, but in this article, we will focus on their simplest non-trivial application — *the dynamic prefix sum problem*:

```cpp
void add(int k, int x); // execute a[k] += x (0-based indexing)
int sum(int k);         // sum of the first k elements (from 0 to k - 1)
```

Note that we have to support two types of queries, which makes this problem multi-dimensional:

- If we only cared about about the cost of *updating the array*, we would store it as it is and [calculated the sum](/hpc/simd/reduction) directly on each `sum` query.
- And if we only cared about the cost of *prefix sum queries*, we would keep it ready and [re-calculate them entirely from scratch](/hpc/algorithms/prefix) on each update.

Both of these options perform $O(1)$ work on one query type but $O(n)$ work on the other. They are only optimal when one type queries is extremely rare. When this is not the case, we can trade off the work on one type of query for increased performance of the other, and segment trees let you do exactly that, achieving the equilibrium of $O(\log n)$ for both queries.

The main idea is this. Calculate the sum of the entire array put it somewhere. Then split it in halves, calculate the sum on both halves, and also store them somewhere. Then split these halves in halves and so on, until we recursively reach segments of length one.

These sequence of computations can be represented as a static-structure tree:

![](../img/segtree-path.png)

Some nice properties of this construct:

1. The tree has at most $2n$ vertices: $n$ on the last layer, $\frac{n}{2}$ on the previous, $\frac{n}{4}$ on the one before that, and so on.
2. The height of the tree is $\Theta(\log n)$ as on each "level" the sizes of the segments halves.
3. Each prefix can be split into $O(\log n)$ non-intersecting segments corresponding to vertices of a segment tree: you need at most one from each layer.

When $n$ is not a perfect power of two, not all levels will be filled entirely. The last layer will be incomplete, but this doesn't take away any of these nice properties that let us solve the problem (look at the bold path on the illustration):

1. Property 1 guarantees that we will need $O(n)$ space to store the tree
2. **Update** query is processed by adding a value to all vertices that correspond to segments that. Property 1 says there will be at most $O(\log n)$ of them.
3. **Prefix sum** query is processed by finding all vertices that compose the prefix and summing the values stored in them. Property 3 says there will also be at most $O(\log n)$ of them.

Note that by the same logic that each prefix can be covered by $O(\log n)$ nodes, each possible segment can also be covered by $O(\log n)$ nodes: you just possibly need at most two of them on each level. This lets us compute sums on any segment, although in this article we are not going to do it, instead reducing it to computing two prefix sums (from the right border, and the subtracting the prefix sum on the left border).

This is a general idea. Many different implementations possible, which we will explore one by one in this article.

<!--

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

The most straightforward way to implement a segment tree is to store everything a node needs explicitly. If you were at an "Introduction to OOP" class, you'd probably implement a segment tree like this:

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
    s = a[lb];
} else {
    int t = (lb + rb) / 2;
    l = new segtree(lb, t);
    r = new segtree(t, rb);
    s = l->s + r->s;
}
```

But to remove complexity, we are going to assume that the array is just zero-initialized in all future implementations.

Now, to implement `add`, we descend down the tree, adding the delta to the `s` field, until we reach a leaf node:

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

To calculate the sum on a segment, we can check if the query covers the current segment fully or doesn't cover at all and return the result for the node right away. If it is not the case, we can recursively call the query on the children and they will figure it out:

```c++
int sum(int lq, int rq) {
    if (rb <= lq && rb <= rq) // if we are fully inside, return the sum
        return s;
    if (rq <= lb || lq >= rb) // if we don't intersect, return zero
        return 0;
    return l->sum(k) + r->sum(k);
}
```

For the prefix sum query, since the left border is always zero, these checks simplify:

```c++
int sum(int k) {
    if (rb <= k)
        return s;
    if (lb >= k)
        return 0;
    return l->sum(k) + r->sum(k);
}
```

Since we have two types of queries, we also got two separate graphs to look at:

![](../img/segtree-pointers.svg)

While this object-oriented implementation is quite good in terms of software engineering practices, there are several aspects that make it terrible in terms of performance:

- Query implementations use [recursion](/hpc/architecture/functions), although the `add` query can be tail-call optimized.
- Query implementations use unpredictable [branching](/hpc/pipelining/branching), stalling the CPU pipeline.
- The nodes stores extra metadata. The structure takes $4+4+4+8+8=28$ bytes and gets padded to 32 bytes for [memory alignment](/hpc/cpu-cache/alignment) reasons, while only 4 bytes are necessary to hold the integer sum.
- And, most importantly, we are doing [pointer chasing](/hpc/cpu-cache/latency) in both queries: we can't descend into children until we fetched their pointers, even though we can precisely infer the segments we need just from the query bounds.

The last issue is the most critical one. To get rid of pointer chasing, we need to get rid of pointers, converting our structure to being implicit.

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

![The nodes comprising the first 7 elements are selected in bold](../img/segtree-ranges.png)

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

As computing the `hole` function is not on the critical path between iteration, it does not introduce any significant overhead, but completely removes the cache associativity problem:

![](../img/segtree-fenwick-holes.svg)

There are still other minor issues with Fenwick trees. Similar to [binary search](../binary-search), the temporal locality of its memory accesses is not great, as rarely accessed elements are grouped with the most frequently accessed ones. It also executes has to perform end-of-loop checks and executes non-constant number of iterations, likely causing a branch mispredict, although just a single one.

But we are going to leave it there and focus on an entirely different approach. If you know [S+ trees](../s-tree), you've probably guessed where this is going.

### Wide Segment Trees

![](../img/segtree-wide.png)

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

```c++
int sum(int k) {
    int res = 0;
    for (int h = 0; h < H; h++)
        res += t[offset(h) + (k >> (h * b))];
    return res;
}
```

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

typedef int vec __attribute__ (( vector_size(32) ));

constexpr int round(int k) {
    return k & ~(B - 1); // = k / B * B
}

void add(int k, int _x) {
    vec x = _x + vec{};
    for (int h = 0; h < H; h++) {
        auto l = (vec*) &t[offset(h) + round(k)];
        auto m = (vec*) T.mask[k % B];
        for (int i = 0; i < B / 8; i++)
            l[i] += x & m[i];
        k >>= b;
    }
}
```

![](../img/segtree-simd.svg)

Wide Fenwick trees make little sense. The speed of Fenwick trees comes from rapidly iterating over just the elements we need.

Unlike [S-trees](../s-tree), you can easily change block size:

![](../img/segtree-simd-others.svg)

### Comparison

![](../img/segtree-popular.svg)

![](../img/segtree-popular-relative.svg)

### Acknowledgements

"[Efficient and easy segment trees](https://codeforces.com/blog/entry/18051)" by Oleksandr Bacherikov 

This article is loosely based on "[Practical Trade-Offs for the Prefix-Sum Problem](https://arxiv.org/pdf/2006.14552.pdf)" by Giulio Ermanno Pibiri and Rossano Venturini. It has some more detailed discussions, as well as some other implementations or branchless top-down segment tree and why b-ary Fenwick tree is not a good idea. Intermediate structures we've skipped here.
