---
title: Models of Computation
weight: 3
draft: true
---

In classical theoretical computer science, really exciting things stopped happening in the 70s; everything past that are just attempts to replace logarithms in the asymptotic with something slightly less than logarithms. If 50 years ago such algorithms had hope that eventually there will be enough computing power to process the large datasets for which they beat their asymptotically inferior, but practical counterparts, nowadays we know for certain that they never will.

This is what this book is about: accepting the reality and optimizing for the hardware you have, beyond just asymptotic complexity. You will probably not learn a single asymptotically faster algorithm here, but you will learn how to squeeze performance from all of non-exponentially-increasing transistors you have, which is a far more impactful skill.

Computers are still getting faster, but in ways orthogonal to the computation model, and we need to create new ones

Why this is important to optimize algorithms beyond Big O.

The goal of this chapter is to explain why this is the case,



It became much more important.


This model worked well *at the time*. Computers and program execution environments are much more complex now.


In this chapter we are going to explore the reasons why this happened.

### Beyond Big O

This was the case. More computers are not tall, they are broad.


The models typically "charge" only one type of operation.

RAM model random-access machines

Word RAM model

External memory model

Different types of parallel RAM model

Communication complexity

There are many other frameworks. Some in terms of cryptography or communication in general. Some work for hardware designers. "Transistor model" that counts the number of transistors, or "energy model" based on physical entropy laws. Quantum algorithms, or maybe even human-executed algorithms, where you also need to care about errors.
