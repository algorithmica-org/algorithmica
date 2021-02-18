---
title: Synchronization Primitives
weight: 2
---

Consider the following loop:

```cpp
int s = 0;

for (int i = 0; i < n; i++) {
    s += a[i];
}
```

We can make it parallel like this:

```cpp
int s = 0;

#pragma omp parallel for
for (int i = 0; i < n; i++) {
    s += a[i];
}
```

This snippet uses OpenMP, which will be covered in the next chapter. What you need to know about it for now is that it spawns a number of threads and distributes work evenly between them. You can write an equivalent function with threads in C++.

The problem
