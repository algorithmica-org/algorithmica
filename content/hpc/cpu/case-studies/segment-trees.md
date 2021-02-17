---
title: Segment Trees
---

## Segment Trees

* Static tree data structure used for storing information about array segments
* Popular in competitive programming, very rarely used in real life
* Built recursively: build a tree for left and right halves and merge results to get root
* Many different implementations possible

![](https://i.stack.imgur.com/xeIcl.png)

----

### Pointer-Based

* Actually really good in terms of SWE practices, but terrible in terms of performance
* Pointer chasing, 4 unnecessary metadata fields, recursion, branching

```cpp
struct segtree {
    int lb, rb; // left and right borders of this segment
    int sum = 0; // sum on this segment
    segtree *l = 0, *r = 0;
    segtree(int _lb, int _rb) {
        lb = _lb, rb = _rb;
        if (lb + 1 < rb) {
            int t = (lb + rb) / 2;
            l = new segtree(lb, t);
            r = new segtree(t, rb);
        }
    }
    void add(int k, int x) {
        sum += x;
        if (l) {
            if (k < l->rb) l->add(k, x);
            else r->add(k, x);
        }
    }
    int get_sum(int lq, int rq) {
        if (lb >= lq && rb <= rq) return sum;
        if (max(lb, lq) >= min(rb, rq)) return 0;
        return l->get_sum(lq, rq) + r->get_sum(lq, rq);
    }
};
```

https://algorithmica.org/ru/segtree

----

### Implicit (Recursive)

* Eytzinger-like layout: $2k$ is the left child and $2k+1$ is the right child
* Wasted memory, recursion, branching

```cpp
int n, t[4 * MAXN];

void build(int a[], int v, int tl, int tr) {
    if (tl == tr)
        t[v] = a[tl];
    else {
        int tm = (tl + tr) / 2;
        build (a, v*2, tl, tm);
        build (a, v*2+1, tm+1, tr);
        t[v] = t[v*2] + t[v*2+1];
    }
}

int sum(int v, int tl, int tr, int l, int r) {
    if (l > r)
        return 0;
	if (l == tl && r == tr)
        return t[v];
    int tm = (tl + tr) / 2;
    return sum (v*2, tl, tm, l, min(r,tm))
         + sum (v*2+1, tm+1, tr, max(l,tm+1), r);
}
```

http://e-maxx.ru/algo/segment_tree

----

### Implicit (Iterative)

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
