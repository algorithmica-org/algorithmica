---
title: Segment Trees
weight: 3
draft: true
---

The lessons we learned from [optimizing](../binary-search) [binary search](../s-tree) can be applied to a broader range of data structures.

In this article, instead of trying to optimize something from the STL, we will focus on the *segment tree* — a structure that may be unfamiliar to most *normal* programmers and perhaps even most computer science researchers[^tcs], but is used very extensively in [programming competitions](https://codeforces.com/) for its speed and simplicity of implementation.

[^tcs]: Segment trees are rarely mentioned in scientific literature because they are relatively novel (invented around 2000), and *asymptotically* don't do anything that [any other binary tree](https://en.wikipedia.org/wiki/Tree_(data_structure)) can't do, but they are much faster *in practice* for the problems they solve.

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

This implementation still has some problems: we are potentially using twice as much memory as necessary, and we still have costly branching. To get rid of these problems, we need to change the approach a little bit.

### Bottom-Up Implementation

* Different layout: leaf nodes are numbered $n$ to $(2n - 1)$, "parent" is $\lfloor k/2 \rfloor$
* Minimum possible amount of memory
* Fully iterative and no branching (pipelinize-able reads!)

```c++
int t[2 * N];

void add(int k, int x) {
    k += N;
    while (k != 0) {
        t[k] += x;
        k >>= 1;
    }
}

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

![](../img/segtree-bottomup.svg)

### Arbitrarily-Sized Arrays

```c++
int sum(int r) {
    r += N - 1;
    int l = N, s = 0;
    while (l <= r) {
        if ( l & 1) s += t[l++];
        if (~r & 1) s += t[r--];
        l >>= 1, r >>= 1;
    }
    return s;
}
```

Magically, it just works

```c++
const int last_layer = 1 << __lg(2 * N - 1);

int leaf(int k) {
    k += last_layer;
    k -= (k >= 2 * N) * N;
    return k;
}

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

Branchless

```c++
int sum(int k) {
    k = leaf(k - 1);
    int s = 0;
    while (k != 0) {
        s += ((k & 1) == 0) * t[k]; // simplify?
        k = (k - 1) >> 1;
    }
    return s;
}
```

![](../img/segtree-branchless.svg)

### Fenwick trees

* Structure used to calculate prefix sums and similar operations
* Defined as array $t_i = \sum_{k=f(i)}^i a_k$ where $f$ is any function for which $f(i) \leq i$
* If $f$ is "remove last bit" (`x -= x & -x`),
  then both query and update would only require updating $O(\log n)$ different $t$'s

![](../img/fenwick-sum.png)
![](../img/fenwick-update.png)

```cpp
int t[N + 1];

void add(int k, int x) {
    for (k += 1; k <= N; k += k & -k)
        t[k] += x;
}

int sum(int k) {
    int res = 0;
    for (; k != 0; k &= k - 1) // k -= k & -k
        res += t[k];
    return res;
}
```

```c++
// how you can use it to calculate sums on subsegments:
int sum (int l, int r) {
    return sum(r) - sum(l-1);
}
```

![](../img/segtree-fenwick.svg)

Can't be more optimal because of pipelining and implicit prefetching

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

![](../img/segtree-fenwick-holes.svg)

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
