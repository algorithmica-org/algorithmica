---
title: Loops and Loop Unrolling
weight: 2
---

Let's consider a slightly more complex example:

```nasm
loop:
    add  edx, DWORD PTR [rax]
    add  rax, 4
    cmp  rax, rcx
    jne  loop
```

It calculates the sum of a 32-bit integer array, just as a simple `for` loop would.

The "body" of the loop is `add edx, DWORD PTR [rax]`. This instruction loads data from the iterator `rax` and adds it to the accumulator `edx`.

Next, we move the iterator 4 bytes forward with `add rax, 4`.

Then a slightly more complicated thing happens. Assembly doesn't have if-s, for-s, functions or other control flow structures that high level languages have. What it does have is `goto`, or "jump", how it is known in the world of low-level programming.

**Jump** "jumps" to location specified by a label, which needs to be declared somewhere else as a string followed by `:`. When converted to machine code, it is replaced by an instruction that moves the instruction pointer by a fixed number of bytes so that it ends up at the instruction pointed by the label.

Label can be any string, but compilers don't get creative with naming and [just use](https://godbolt.org/z/T45x8GKa5) the `.Ln` pattern for loops, where `n` is the line number in the source, and function names with their signatures when picking names for labels.

**Unconditional** jump `jmp` can only be used to implement `while (true)` kind of loops or stitch parts of a program together. A family of **conditional** jumps is used to implement actual control flow.

It is reasonable to think that these conditions are computed as `bool`-s somewhere and passed to conditional jumps as operands: after all, this is how it works in programming languages. But that is not how it is implemented in hardware. Conditional operations use a special `FLAGS` register, which first needs to be populated by executing certain instructions that perform some kind of checks.

In our example, `cmp rax, rcx` compares the iterator `rax` with the end-of-array pointer `rcx`. This updates the flags register, and now it can be used by `jne loop`, which looks up a certain bit there that tells whether the two values are equal or not, and then either jumps back to the beginning or continues to the next instruction, thus breaking the loop.

### Loop Unrolling

One thing you might have noticed about the loop above is that there is a lot of overhead to process a single element. During each cycle, there is only one useful instruction executed, and the other 3 are maintaining the iterator and trying to find out if we are done yet.

What we can do is to *unroll* the loop by grouping iterations together — equivalent to writing something like this in C:

```c++
for (int i = 0; i < n; i += 4) {
    s += a[i];
    s += a[i + 1];
    s += a[i + 2];
    s += a[i + 3];
}
```

In assembly, it would look something like this:

```nasm
loop:
    add  edx, [rax]
    add  edx, [rax+4]
    add  edx, [rax+8]
    add  edx, [rax+12]
    add  rax, 16
    cmp  rax, rsi
    jne  loop
```

Now we only need 3 loop control instructions for 4 useful ones (improvement from $\frac{1}{4}$ to $\frac{4}{7}$ in terms of efficiency), and this can be continued to reduce the overhead almost to zero.

In practice though, unrolling loops isn't always necessary for performance because of a mechanism called *out-of-order execution*. Modern processors don't actually execute instructions one-by-one, but maintain a "pool" of pending instructions so that two independent operations can be executed concurrently without waiting for each other to finish.

This is our case too: the real speedup from unrolling won't be fourfold, because incrementing the counter and checking for end of loop are independent from the loop body and can be scheduled to run concurrently with it.
