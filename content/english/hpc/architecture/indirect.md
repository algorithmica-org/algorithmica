---
title: Indirect Branching
weight: 4
---

During assembly, all labels are converted to addresses (absolute or relative) and then encoded into jump instructions.

You can also jump by a non-constant value stored inside a register, which is called a *computed jump*:

```nasm
jmp rax
```

This has a few interesting applications related to dynamic languages and implementing more complex control flow.

### Multiway Branch

If you have already forgotten what a `switch` statement does, here is a little subroutine for calculating GPA in the American grading system:

```cpp
switch (grade) {
    case 'A':
        return 4.0;
        break;
    case 'B':
        return 3.0;
        break;
    case 'C':
        return 2.0;
        break;
    case 'D':
        return 1.0;
        break;
    case 'E':
    case 'F':
        return 0.0;
        break;
    default:
        return NAN;
}
```

I personally don't remember the last time I used a switch in a non-educational context. In general, switch statements are equivalent to a sequence of "if, else if, else if, else if…" and so on, and for this reason many languages don't even have them. Nonetheless, such control flow structures are important for implementing parsers, interpreters, and other state machines, which are often comprised of a single `while (true)` loop and a `switch (state)` statement inside.

When we have control over the range of values that the variable can take, we can use the following trick utilizing computed jumps. Instead of making $n$ conditional branches, we can create a *branch table* that contains pointers/offsets to possible jump locations, and then just index it with the `state` variable taking values in the $[0, n)$ range.

Compilers use this technique when the values are densely packed together (not necessarily strictly sequentially, but it has to be worth having blank fields in the table). It can also be implemented explicitly with a *computed goto*:

```cpp
void weather_in_russia(int season) {
    static const void* table[] = {&&winter, &&spring, &&summer, &&fall};
    goto *table[season];

    winter:
        printf("Freezing\n");
        return;
    spring:
        printf("Dirty\n");
        return;
    summer:
        printf("Dry\n");
        return;
    fall:
        printf("Windy\n");
        return;
}
```

Switch-based code is not always straightforward for compilers to optimize, so in the context of state machines, `goto` statements are often used directly. The I/O-related part of `glibc` is full of examples.

### Dynamic Dispatch

Indirect branching is also instrumental in implementing runtime polymorphism.

Consider the cliché example when we have an abstract class of `Animal` with a virtual `.speak()` method, and two concrete implementations: a `Dog` that barks and a `Cat` that meows:

```cpp
struct Animal {
    virtual void speak() { printf("<abstract animal sound>\n");}
};

struct Dog : Animal {
    void speak() override { printf("Bark\n"); }
};

struct Cat : Animal {
    void speak() override { printf("Meow\n"); }
};
```

We want to create an animal and, without knowing its type in advance, call its `.speak()` method, which should somehow invoke the right implementation:

```c++
Dog sparkles;
Cat mittens;

Animal *catdog = (rand() & 1) ? (Animal*)&sparkles : (Animal*)&mittens;
catdog->speak();
```

There are many ways to implement this behavior, but C++ does it using a *virtual method table*.

For all concrete implementations of `Animal`, compiler pads all their methods (that is, their instruction sequences) so that they have the exact same length for all classes (by inserting some [filler instructions](../layout) after `ret`) and then just writes them sequentially somewhere in the instruction memory. Then it adds a *run-time type information* field to the structure (that is, to all its instances), which is essentially just the offset in the memory region that points to the right implementation of the virtual methods of the class.

With a virtual method call, that offset field is fetched from the instance of a structure and a normal function call is made with it, using the fact that all methods and other fields of every derived class have exactly the same offsets.

Of course, this adds some overhead:

- You may need to spend another 15 cycles or so for the same pipeline flushing reasons as for [branch misprediction](/hpc/pipelining).
- The compiler most likely won't be able to inline the function call itself.
- Class size increases by a couple of bytes or so (this is implementation-specific).
- The binary size itself increases a little bit.

For these reasons, runtime polymorphism is usually avoided in performance-critical applications.
