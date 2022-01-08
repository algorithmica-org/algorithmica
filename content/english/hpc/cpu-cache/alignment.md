---
title: Data Alignment
weight: 6
---

The fact that the memory is split into cache lines has huge implications on data structure layout. If you need to retrieve a certain atomic object, such as a 32-bit integer, you want to have it all located in a single cache line: both because hardware stitching results together takes precious transistor space and because retrieving 2 cache lines is slow and increases memory bandwidth. The "natural" alignment of `int` is 4 bytes.

For this reason, in C and most other programming languages structures by default pad structures with blank bytes in order to insure that every data member will not be split by a cache line boundary. Instead of playing a complex tetris game and rearranging its members, it simply pads each element so that the alignment of the next one matches its "natural" one. In addition, the data structure as a whole may be padded with a final unnamed member to allow each member of an array of structures to be properly aligned.

Consider the following toy example:

```cpp
struct Data {
    char a;
    short b;
    int c;
    char d;
};
```

When stored succinctly, it needs a total of $1 + 2 + 4 + 1 = 8$ bytes per instance, but doing so raises a few issues. Assuming that the whole structure has alignment of 4 (its largest member, `int`), `a` is fine, but `b`, `c` and `d` are not aligned.

To fix this, compiler inserts unnamed members so that each next unaligned member gets to its alignment:

```cpp
struct Data {
    char a;    // 1 byte
    char x[1]; // 1 byte for the following 'short' to be aligned on a 2 byte boundary
    short b;   // 2 bytes 
    int c;     // 4 bytes - largest structure member
    char d;    // 1 byte
    char y[3]; // 3 bytes to make total size of the structure 12 bytes (divisible by 4)
};
```

Padding is only inserted when a structure member is followed by a member with a larger alignment requirement or at the end of the structure. By changing the ordering of members in a structure, it is possible to change the amount of padding required to maintain alignment. For example, if members are sorted by descending alignment requirements a minimal amount of padding is required. The minimal amount of padding required is always less than the largest alignment in the structure. Computing the maximum amount of padding required is more complicated, but is always less than the sum of the alignment requirements for all members minus twice the sum of the alignment requirements for the least aligned half of the structure members.

By default, when you allocate an array, the only guarantee about its alignment you get is that none of its elements are split by a cache line. For an array of `int`, this means that it gets the alignment of 4 bytes (`sizeof int`), which lets you load exactly one cache line when reading any element.

Alignment requirements can be declared not only for the data type, but for a particular variable. The typical use cases are allocating something the beginning of a 64-byte cache line, 32-byte SIMD block or a 4K memory page.

```cpp
alignas(64) float a[n];
```

For allocating an array dynamically, we can use `std::aligned_alloc` which takes the alignment value and the size of array in bytes, and returns a pointer to the allocated memory (just like `new` does), which should be explicitly deleted when no longer used.
