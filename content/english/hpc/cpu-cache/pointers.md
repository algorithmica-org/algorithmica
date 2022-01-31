---
title: Pointer Alternatives
weight: 6
---


Memory addressing operator is fused on x86, so `k = q[k]` folds into one terse `mov rax, DWORD PTR q[0+rax*4]` instruction, although it does a multiplication by 4 and an addition under the hood. Although fully fused, These additional computations actually add some delay to memory operations, and in fact the latency of L1 fetch is 4 or 5 cycles — the latter being the case if we need to perform complex computation of address. For this reason, the permutation benchmark measures 3ns or 6 cycles per fetch: 5 for the read (including +1 for address computation) and 1 to move the result to the right register.

We can make our benchmark run slightly faster if we replace "fake pointers" — indices — with actual pointers. There are some syntactical issues in getting "pointer to pointer to pointer…" constructions to work, so instead we will define a struct type that just wraps a pointers to its own kind — this is how most pointer chasing works anyway:

```cpp
struct node { node* ptr; };
```

Now we randomly fill our array with pointers and chase them instead:

```cpp
node* k = q + p[N - 1];

for (int i = 0; i < N; i++)
    k = k->ptr = q + p[i];

for (int i = 0; i < N; i++)
    k = k->ptr;
```

This code now runs in 2ns / 4 cycles for arrays that fit in L1 cache. Why not 4+1=5? Because Zen 2 [has an interesting feature](https://www.agner.org/forum/viewtopic.php?t=41) that allows zero-latency reuse of data accessed just by address, so the "move" here is transparent, resulting in whole 2 cycles saved.

Unfortunately, there is a problem with it on 64-bit systems as the pointers become twice as large, making the array spill out of cache much sooner compared to using a 32-bit index. Graph looks like if it was shifted by one power of two to the left — exactly like it should.

![](../img/permutation-p64.svg)

This problem is mitigated by switching to 32-bit mode. You need to go [through some trouble](https://askubuntu.com/questions/91909/trouble-compiling-a-32-bit-binary-on-a-64-bit-machine) getting 32-bit libs to get this running on a computer made in this century, but this is justified by the result — unless you also need to interoperate with 64-bit software or access more than 4G or RAM.

![](../img/permutation-p32.svg)

The fact that on larger problem sizes the performance is bottlenecked by memory rather than CPU lets us to try something even more stranger: using less than 4 bytes for storing indices. This can be done with bit fields:

```cpp
struct __attribute__ ((packed)) node { int idx : 24; };
```

You don't need to do anything other than defining a structure for the bit field. The CPU does truncation by itself.

```cpp
int k = p[N - 1];

for (int i = 0; i < N; i++) {
    k = q[k].idx = p[i];

for (int i = 0; i < N; i++) {
    k = q[k].idx;
```

This measures at 6.5ns in the L1 cache, but the conversion procedure chosen by the compiler is suboptimal: it is done by loading 3 bytes, which is not optimal. Instead, we could just load a 4-byte integer and truncate it ourselves (we also need to add one more element to the `q` array to ensure we own that extra one byte of memory):

```cpp
k = *((int*) (q + k));
k &= ((1<<24) - 1);
```

It now runs in 4ns, and produces the following graph:

![](../img/permutation-bf-custom.svg)

In short: for something very small, use pointers; for something very large, use bit fields.
