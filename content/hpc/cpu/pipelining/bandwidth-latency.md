---
title: Bandwidth and Latency
weight: 1
---

Bandwidth is the rate at which data can be read or stored. For the purpose of designing algorithms, a more important characteristic is the bandwidth-latency product which basically tells how many cache lines you can request while waiting for the first one without queueing up. It is around 5 or more on most systems. This is like having friends whom you can send for beers asynchronously.


### Prefetching*

What you write:

```cpp
for (int i = 0; i < n; i++) {
    do_stuff(a[i]);
}
```

What compiler does:

```cpp
for (int i = 0; i < n; i++) {
    if (int(&a[i]) % BLOCK_SIZE == 0)
        __builtin_prefetch(&a[i] + BLOCK_SIZE);;
    do_stuff(a[i]);
}
```

You can request more than one block at a time, but we forget about it for now
