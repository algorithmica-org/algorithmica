---
title: Segment Trees
weight: 3
draft: true
---

The lessons we learned from studying layouts for binary search can be applied to broader range of data structures.

Most of examples in this section are about optimizing some algorithms that are either included in standard library or take under 10 lines of code to implement naively, but we will start off with a bit more obscure example.

There are many things segment trees can do. Persistent structures, computational geometry. But for most of this article, we will focus on the dynamic (as opposed to static) prefix sum problem.

Segment tree is a data structure that stores information about array segments. It is a static tree of degree two, and here is what this means:

Segment trees are used for windowing queries or range queries in general, either by themselves or as part of a larger algorithm. They are very rarely mentioned in scientific literature, because they are relatively novel (invented around 2000), and *asymptotically* they don't do anything that any other binary tree can't, but they are dominant structure in the world of competitive programming because of their performance and ease of implementation.

Enable [hugepages](/hpc/cpu-cache/paging) system-wide and forget about it.

Functional programming, e. g. for implementing persistent arrays and derived structures.

Segment trees are built recursively: build a tree for left and right halves and merge results to get root.

```cpp
void add(int k, int x); // 0-based indexation
int sum(int k); // sum of elements indexed [0, k]
```

Static tree data structure used for storing information about array segments. Popular in competitive programming, very rarely used in real life. Many different implementations possible, which we will explore in this article.

![](https://i.stack.imgur.com/xeIcl.png)

## Pointer-Based Implementation

If you were at an "Introduction to OOP" class, you would probably implement a segment tree like this:

```c++
struct segtree {
    int lb, rb;
    int s = 0;
    segtree *l = nullptr, *r = nullptr;

    segtree(int lb, int rb) : lb(lb), rb(rb) {
        if (lb + 1 < rb) {
            int t = (lb + rb) / 2;
            l = new segtree(lb, t);
            r = new segtree(t, rb);
        }
    }
    
    void add(int k, int x) {
        s += x;
        if (l != nullptr) {
            if (k < l->rb)
                l->add(k, x);
            else
                r->add(k, x);
        }
    }
    
    int sum(int k) {
        if (rb <= k)
            return s;
        if (lb >= k)
            return 0;
        return l->sum(k) + r->sum(k);
    }
};
```

![](../img/segtree-pointers.svg)

It takes 4+4+4+8+8=28 bytes, although they get padded to 32 for [memory alignment](/hpc/cpu-cache/alignment) reasons.

Actually really good in terms of SWE practices, but terrible in terms of performance
Pointer chasing, 4 unnecessary metadata fields, recursion, branching

## Implicit Segment Trees

Eytzinger-like layout: $2k$ is the left child and $2k+1$ is the right child.

```c++
int t[4 * N];

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

![](../img/segtree-topdown.svg)

Still have wasted memory.

### Iterative Implementation

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

![](../img/segtree-iterative.svg)

### Implicit (Bottom-up)

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

## Fenwick trees

* Structure used to calculate prefix sums and similar operations
* Defined as array $t_i = \sum_{k=f(i)}^i a_k$ where $f$ is any function for which $f(i) \leq i$
* If $f$ is "remove last bit" (`x -= x & -x`),
  then both query and update would only require updating $O(\log n)$ different $t$'s

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
