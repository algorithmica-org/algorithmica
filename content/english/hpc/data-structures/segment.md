---
title: Segment Trees
weight: 2
---

The lessons we learned from studying layouts for binary search can be applied to broader range of data structures.

Most of examples in this section are about optimizing some algorithms that are either included in standard library or take under 10 lines of code to implement naively, but we will start off with a bit more obscure example.

Segment tree is a data structure that stores information about array segments. It is a static tree of degree two, and here is what this means:

Segment trees are used for windowing queries or range queries in general, either by themselves or as part of a larger algorithm. They are very rarely mentioned in scientific literature, because they are relatively novel (invented around 2000), and *asymptotically* they don't do anything that any other binary tree can't, but they are dominant structure in the world of competitive programming because of their performance and ease of implementation.

Segment trees are built recursively: build a tree for left and right halves and merge results to get root.

```cpp
void add(int k, int x); // 0-based indexation
int sum(int k); // sum of elements indexed [0, k]
```

## Segment Trees

* Static tree data structure used for storing information about array segments
* Popular in competitive programming, very rarely used in real life
* 
* Many different implementations possible

![](https://i.stack.imgur.com/xeIcl.png)

----

### Pointer-Based

* Actually really good in terms of SWE practices, but terrible in terms of performance
* Pointer chasing, 4 unnecessary metadata fields, recursion, branching

```cpp
struct segtree {
    int lb, rb;
    int s = 0;
    segtree *l = 0, *r = 0;

    segtree(int lb, int rb) : lb(lb), rb(rb) {
        if (lb + 1 < rb) {
            int t = (lb + rb) / 2;
            l = new segtree(lb, t);
            r = new segtree(t, rb);
        }
    }
    
    void add(int k, int x) {
        s += x;
        if (l) {
            if (k < l->rb)
                l->add(k, x);
            else
                r->add(k, x);
        }
    }
    
    int sum(int k) { // [0, k)
        if (rb <= k)
            return s;
        if (lb >= k)
            return 0;
        return l->sum(k) + r->sum(k);
    }
};
```

----

### Implicit (Recursive)

* Eytzinger-like layout: $2k$ is the left child and $2k+1$ is the right child
* Wasted memory, recursion, branching

```cpp
int t[4 * N];

void _add(int k, int x, int v = 1, int l = 0, int r = N) {
    t[v] += x;
    if (l + 1 < r) {
        int m = (l + r) / 2;
        if (k < m)
            _add(k, x, 2 * v, l, m);
        else
            _add(k, x, 2 * v + 1, m, r);
    }
}

int _sum(int k, int v = 1, int l = 0, int r = N) {
    if (l > k)
        return 0;
    if (r - 1 <= k)
        return t[v];
    int m = (l + r) / 2;
    return _sum(k, 2 * v, l, m)
         + _sum(k, 2 * v + 1, m, r);
}
```

### Implicit (Iterative)

```cpp
void add(int k, int x) {
    int v = 1, l = 0, r = N;
    while (l + 1 < r) {
        t[v] += x;
        int m = (l + r) / 2;
        if (k < m)
            v = 2 * v, r = m;
        else
            v = 2 * v + 1, l = m;
    }
    t[v] += x;
}

int sum(int k) {
    if (k == N - 1)
        return t[1];
    int v = 1, l = 0, r = n;
    int s = 0;
    while (l < r) {
        int m = (l + r) / 2;
        v *= 2;
        if (k < m) {
            if (k == m - 1)
                return s + t[v];
            r = m;
        } else {
            s += t[v];
            v++;
            l = m;
        }
    }
    return s;
}
```
### Implicit (Bottom-up)

* Different layout: leaf nodes are numbered $n$ to $(2n - 1)$, "parent" is $\lfloor k/2 \rfloor$
* Minimum possible amount of memory
* Fully iterative and no branching (pipelinize-able reads!)

```cpp
int n, t[2*maxn];

void build() {
    for (int i = n-1; i > 0; i--)
        t[i] = max(t[i<<1], t[i<<1|1]);
}

void upd(int k, int x) {
    k += n;
    t[k] = x;
    while (k > 1) {
        t[k>>1] = max(t[k], t[k^1]);
        k >>= 1;
    }
}

int rmq(int l, int r) {
    int ans = 0;
    l += n, r += n;
    while (l <= r) {
        if (l&1)    ans = max(ans, t[l++]);
        if (!(r&1)) ans = max(ans, t[r--]);
        l >>= 1, r >>= 1;
    }
    return ans;
}
```

https://codeforces.com/blog/entry/18051

---

## Fenwick trees

* Structure used to calculate prefix sums and similar operations
* Defined as array $t_i = \sum_{k=f(i)}^i a_k$ where $f$ is any function for which $f(i) \leq i$
* If $f$ is "remove last bit" (`x -= x & -x`),
  then both query and update would only require updating $O(\log n)$ different $t$'s

```cpp
int t[maxn];

// calculate sum on prefix:
int sum(int r) {
    int res = 0;
    for (; r > 0; r -= r & -r)
        res += t[r];
    return res;
}

// how you can use it to calculate sums on subsegments:
int sum (int l, int r) {
    return sum(r) - sum(l-1);
}

// updates necessary t's:
void add(int k, int x) {
    for (; k <= n; k += k & -k)
        t[k] += x;
}
```

Can't be more optimal because of pipelining and implicit prefetching

## Further Reading

This article is loosely based on "[Practical Trade-Offs for the Prefix-Sum Problem](https://arxiv.org/pdf/2006.14552.pdf)" by Giulio Ermanno Pibiri and Rossano Venturini.
