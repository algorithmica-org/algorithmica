---
title: Data Packing
weight: 7
---

If you know what you are doing, you can turn disable padding and instead pack you data structure as tight as possible. This is done

When loading it though, the

```cpp
struct __attribute__ ((packed)) Data {
    char a;
    short b;
    int c;
    char d;
};
```

This is a less standardized feature, but you can also use it with *bit fields* to members of less than fixed size.

```cpp
struct __attribute__ ((packed)) Data {
    char a;     // 1 byte
    int b : 24; // 3 bytes
};
```

The structure takes 4 bytes when packed and 8 bytes when padded. This feature is not so widespread because CPUs don't have 3-byte arithmetic and has to do some inefficient conversion during loading:

```cpp
int load(char *p) {
    char x = p[0], y = p[1], z = p[2];
    return (x << 16) + (y << 8) + z;
}
```

This can be optimized by loading a 4-byte `int` and then using a mask to discard its highest bits.

```cpp
int load(int *p) {
    int x = *p;
    return x & ((1<<24) - 1);
}
```

Compilers usually don't do that, because this is not technically legal sometimes: may not own that 4th byte, and won't let you load it even if you are discarding it.
