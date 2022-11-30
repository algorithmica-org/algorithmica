---
title: Preface
weight: -1
ignoreIndexing: true
draft: true
---

There are two influential textbooks on computer science: one was written 30 years ago, and the other was written 50 years ago. Computers were very different back then.

A lot of this book discusses hardware. I am a software developer with no formal training in hardware, so on some occasions I might be misleading or wrong. All I am trying to do is to help you build a useful mental model.

## Prerequisites

Its intended audience is everyone from performance engineers and practical algorithm researchers to undergraduate computer science students who have just finished an advanced algorithms course and want to learn more practical ways to speed up a program than by going from $O(n \log n)$ to $O(n \log \log n)$.

### How to Read This Book

There are a lot of forward references I couldn't get rid of.

Read some of the SIMD and memory chapter first.

Chapter 1 is a "why you should care" sort of read.

Chapter 2 is an introduction to computer architectures from the perspective of performance. There is a high chance that you already know it from a college course, but I still advise to read it to get into context, as we will cover assembly-level optimization techniques there.

Chapter 3 is where experienced programmers should start from.

Chapter 4 discusses compilation with the example of C++ and GCC/Clang. Chapter 5 discusses language-agnostic profiling methods. You are free to skip both.

Chapter 6 discusses arithmetic and chapter 7 discusses modular arithmetic and its applications. They also acts as a sort of reference for algorithms in the case studies.

Chapter 8 introduces the external memory model and how the memory system works. Chapter 9 follows up with experimental studies of how it can affect performance.

Chapters 10 discusses SIMD programming, which is a major part. It is not *that* intertwined with the preivous ones, and if you are feeling comfortable, I'd suggest that you start reading with it because it will teach you powerful techniques right away.

Chapters 11-12 contain case studies of complex algorithms. Performance engineering is a practical field, so you should learn from major examples.

The first 5 chapters build up general understanding of performance.

Chapters 6-10 go deeper into modern features. Arithmetic, number theory (the techniques that are also relevant outside of it). Some are theoretic, and then applied in practice.

Chapters 11 and 12 contain case studies of complex algorithms and data structures. This is scientifically novel part of the book.

## Scope

In the first part, we are mainly concerned with single-core CPU programming.

## Acknowledgements

A lot of illustrations are borrowed from other places on the internet. They are meant to be temporary placeholders.

## How to Support

All materials are hosted on GitHub, with code in a [separate repository](https://github.com/sslotin/scmm-code). This isn't a collaborative project, but any contributions and feedback are very much welcome.
