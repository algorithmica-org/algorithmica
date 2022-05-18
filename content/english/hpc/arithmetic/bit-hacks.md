---
title: Bit Manipulation
weight: 7
draft: true
---

This article is largely based on [Bit Twiddling Hacks](https://graphics.stanford.edu/~seander/bithacks.html) by Sean Eron Anderson. Some methods were added, and some removed due to being solved by hardware. Most of these are already optimized by compilers.

A lot of it became obsolete on architectures where `cmov` is available.

This also serves as an exercise.

## Basic Operations

`>>`

Note that arithmetic shift shifts in `1` for negative numbers and in `0` for positive ones. (although it can be implementation-defined?)

Left or right-shifting negative numbers invokes undefined behavior in C/C++.

`<<`

`rol` instruction that does "rotate left"

`__builtin_popcount` `popcnt` Returns the number of 1-bits in x.

`__builtin_parity` Returns the *parity* of x (that is, the number of 1-bits in x modulo 2).

This is presumably for [error detection](https://en.wikipedia.org/wiki/Parity_bit).

`__builtin_clrsb` Returns the number of leading redundant sign bits in x, i.e., the number of bits following the most significant bit that are identical to it. There are no special cases for 0 or other values.

`__builtin_ffs` Returns one plus the index of the least significant 1-bit of x, or if x is zero, returns zero.

`__builtin_clz` Returns the number of leading 0-bits in x, starting at the most significant bit position. If x is 0, the result is undefined

`__builtin_ctz` Returns the number of trailing 0-bits in x, starting at the least significant bit position. If x is 0, the result is undefined

`ctz`, `clz` -> `__lg`

## Recipes

### Sign of an integer

`(x < 0)` or `x >> 31`

### Check if two integers have the same sign

`x ^ z < 0`

### Absolute value of an integer

Extract the sign bit: `int mask = x >> 31`. This will be `1` for negative numbers and `0` for positive.

XOR it with the initial number: `x ^ mask` (which equates to either adding or subtracting 1 depending on the sign).

Subtract mask from the result of step 2: `(x ^ mask) - mask`

Alternatively, you can use `(v + mask) ^ mask` which does the same but in reverse.

### Get last 1-bit

`x & -x`

### Remove the last 1-bit of an integer

`x & (x - 1)`

### Checking for power of two

`(x & (x - 1)) == 0`

Note that 0 will be considered a power of 2 as well. 

### Reversing bits

Clang has `__builtin_bitreverse{8,16,32,64}`

```c++
int reverseBits(int x)
{
	unsigned int s = sizeof(x) * 8;
	T mask = ~T(0);
	while ((s >>= 1) > 0)
	{
		mask ^= mask << s;
		x = ((x >> s) & mask) | ((x << s) & ~mask);
	}
	return x;
}
```

### Swapping numbers with xor

You've probably heard of this one.

```c++
a ^= b;
b ^= a;
a ^= b;
```

This isn't how it is performed under the hood. There is a separate xchng instruction.

### Modulus a power of two

If `m = (1 << k)`, then `x % m` is the same as `x & (m - 1)`.

## Masks

Masking operations.

### Brute forcing

You can either go recursive (which is obviously slow). You can also go branchless.

Knapsack problem has a brute force solution $O(2^n)$.

```c++
int ans = 0;
for (int mask = 0; mask < (1 << n); mask++) {
    int s = 0;
    for (int i = 0; i < n; i++)
        if (mask >> i & 1)
            s += a[i];
    if (s <= C)
        ans = max(ans, s);
}
```

### Subsets of all subsets

```c++
for (int submask = mask; submask != 0; submask = (submask - 1) & mask) {
    // ...
}
```

It turns out that the total will be $3^n$. Each bit on each iteration can be in one of three states: not in $m$, not in $s$ yet, in both $s$ and $m$. As there are $n$ bit in total, there can be at most $3^n$ different combinations.
