---
title: Alignment and Packing
weight: 8
---

The fact that the memory is partitioned into 64B [cache lines](../cache-lines) makes it difficult to operate on data words that cross a cache line boundary. When you need to retrieve some primitive type, such as a 32-bit integer, you really want to have it located on a single cache line — both because retrieving two cache lines requires more memory bandwidth and stitching the results in hardware requires precious transistor space.

This aspect heavily influences algorithm designs and how compilers choose the memory layout of data structures.

### Aligned Allocation

By default, when you allocate an array of some primitive type, you are guaranteed that the addresses of all elements are a multiple of their size, which ensures that they only span a single cache line. For example, you are guaranteed the address of the first and every other element of an `int` array is a multiple of 4 bytes (`sizeof int`).

Sometimes you need to ensure that this minimum alignment is higher. For example, many [SIMD](/hpc/simd) applications read and write data in blocks of 32 bytes, and it is [crucial for performance](/hpc/simd/moving) that these 32 bytes belong to the same cache line. In such cases, you can use the `alignas` specifier when defining a static array variable:

```c++
alignas(32) float a[n];
```

To allocate a memory-aligned array dynamically, you can use `std::aligned_alloc`, which takes the alignment value and the size of an array in bytes and returns a pointer to the allocated memory — just like the `new` operator does:

```c++
void *a = std::aligned_alloc(32, 4 * n);
```

You can also align memory to sizes [larger than the cache line](../paging). The only restriction is that the size parameter must be an integral multiple of alignment.

You can also use the `alignas` specifier when defining a `struct`:

```c++
struct alignas(64) Data {
    // ...
};
```

Whenever an instance of `Data` is allocated, it will be at the beginning of a cache line. The downside is that the effective size of the structure will be rounded up to the nearest multiple of 64 bytes. This has to be done so that, e.g., when allocating an array of `Data`, not just the first element is properly aligned.

### Structure Alignment

This issue becomes more complicated when we need to allocate a group of non-uniform elements, which is the case for structures. Instead of playing Tetris trying to rearrange the members of a `struct` so that each of them is within a single cache line — which isn't always possible as the structure itself doesn't have to be placed on the start of a cache line — most C/C++ compilers also rely on the mechanism of memory alignment.

Structure alignment similarly ensures that the address of all its member primitive types (`char`, `int`, `float*`, etc) are multiples of their size, which automatically guarantees that each of them only spans one cache line. It achieves that by:

- *padding*, if necessary, each structure member with a variable number of blank bytes to satisfy the alignment requirement of the next member;
- setting the alignment requirement of the structure itself to the maximum of the alignment requirements of its member types, so that when an array of the structure type is allocated or it is used as a member type in another structure, the alignment requirements of all its primitive types are satisfied.

For better understanding, consider the following toy example:

```cpp
struct Data {
    char a;
    short b;
    int c;
    char d;
};
```

When stored succinctly, this structure needs a total of $1 + 2 + 4 + 1 = 8$ bytes per instance, but even assuming that the whole structure has the alignment of 4 bytes (its largest member, `int`), only `a` will be fine, while `b`, `c` and `d` are not size-aligned and potentially cross a cache line boundary.

To fix this, the compiler inserts some unnamed members so that each next member gets the right minimum alignment:

```cpp
struct Data {
    char a;    // 1 byte
    char x[1]; // 1 byte for the following "short" to be aligned on a 2-byte boundary
    short b;   // 2 bytes 
    int c;     // 4 bytes (largest member, setting the alignment of the whole structure)
    char d;    // 1 byte
    char y[3]; // 3 bytes to make total size of the structure 12 bytes (divisible by 4)
};

// sizeof(Data) = 12
// alignof(Data) = alignof(int) = sizeof(int) = 4
```

This potentially wastes space but saves a lot of CPU cycles. This trade-off is mostly beneficial, so structure alignment is enabled by default in most compilers.

### Optimizing Member Order

Padding is only inserted before a not-yet-aligned member or at the end of the structure. By changing the ordering of members in a structure, it is possible to change the required number of padding bytes and the total size of the structure.

In the previous example, we could reorder the structure members like this:

```c++
struct Data {
    int c;
    short b;
    char a;
    char d;
};
```

Now, each of them is aligned without any padding, and the size of the structure is just 8 bytes. It seems stupid that the size of a structure and consequently its performance depends on the order of definition of its members, but this is required for binary compatibility.

As a rule of thumb, place your type definitions from largest data types to smallest — this greedy algorithm is guaranteed to work unless you have some weird non-power-of-two type sizes such as the [10-byte](/hpc/arithmetic/ieee-754#float-formats) `long double`[^extended].

[^extended]: The 80-bit `long double` takes *at least* 10 bytes, but the exact format is up to the compiler — for example, it may pad it to 12 or 16 bytes to minimize alignment issues (64-bit GCC and Clang use 16 bytes by default; you can override this by specifying one of `-mlong-double-64/80/128` or `-m96/128bit-long-double` [options](https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html)).

<!--

For example, if members are sorted by descending alignment requirements a minimal amount of padding is required. The minimal amount of padding required is always less than the largest alignment in the structure. Computing the maximum amount of padding required is more complicated, but is always less than the sum of the alignment requirements for all members minus twice the sum of the alignment requirements for the least aligned half of the structure members.


```c++
struct NodeF {
    int* i1;
    bool b1;
    int* i2;
    bool b2;
    int* i3;
    bool b3;
    int* i4;
    bool b4;
    int* i5;
    bool b5;
};
```

12x8 = 80 bytes.

```c++
struct NodeG {
    int* i1;
    int* i2;
    int* i3;
    int* i4;
    int* i5;
    bool b1;
    bool b2;
    bool b3;
    bool b4;
    bool b5;
};
```

-->

### Structure Packing

If you know what you are doing, you can disable structure padding and pack your data as tight as possible.

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

Compilers usually don't do that because it's technically not legal: that 4th byte may be on a memory page that you don't own, so the operating system won't let you load it even if you are going to discard it right away.
