---
title: Structure Packing
weight: 5
---

If you know what you are doing, you can disable [structure padding](../alignment) and pack your data as tight as possible.

You have to ask the compiler to do it, as such functionality is not a part of neither C nor C++ standard yet. In GCC and Clang, this is done with the `packed` attribute:

```cpp
struct __attribute__ ((packed)) Data {
    long long a;
    bool b;
};
```

This makes the instances of `Data` take just 9 bytes instead of the 16 required by alignment, at the cost of possibly fetching two cache lines to reads its elements.

### Bit fields

You can also use packing along with *bit fields*, which allow you to explicitly fix the size of a member in bits:

```cpp
struct __attribute__ ((packed)) Data {
    char a;     // 1 byte
    int b : 24; // 3 bytes
};
```

This structure takes 4 bytes when packed and 8 bytes when padded. The number of bits a member has doesn't have to be a multiple of 8, and neither does the total structure size. In an array of `Data`, the neighboring elements will be "merged" in the case of a non-whole number of bytes. It also allows you to set a width that exceeds the base type, which acts as padding — although it throws a warning in the process.

<!-- TODO: verify this -->

This feature is not so widespread because CPUs don't have 3-byte arithmetic or things like that and has to do some inefficient byte-by-byte conversion during loading:

```cpp
int load(char *p) {
    char x = p[0], y = p[1], z = p[2];
    return (x << 16) + (y << 8) + z;
}
```

The overhead is even larger when there is a non-whole byte — it needs to be handled with a shift and an and-mask.

This procedure can be optimized by loading a 4-byte `int` and then using a mask to discard its highest bits.

```cpp
int load(int *p) {
    int x = *p;
    return x & ((1<<24) - 1);
}
```

Compilers usually don't do that because this is not technically always legal: that 4th byte may be on a memory page that you don't own, so the operating system won't let you load it even if you are going to discard it right away.
