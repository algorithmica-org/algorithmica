---
title: Instruction-Level Parallelism
weight: 3
---

As a everyday metaphor, consider how a university works. It could have one student at a time and around 50 professors, which would take turns in tutoring, but this would be highly inefficient and result in one bachelor's degree every 4 year.

Maybe this is how the members of the British royal family study.

But for better of worse, the education is scaled.

Instead, universities do two smart things:

1. They teach to large groups of students at once instead of individuals.
2. They overlap their "classes" so that each can all professors keep busy. This way you can increase throughput by 4x.


For the first trick, the CPU world analogue is SIMD, which we covered in the previous chapter. And for the second, it is the technique called pipelining, which we are going to discuss next.

### Instruction Pipelining

The same things applies to CPUs and other hardware. To increase the utilization, instructions are processed in a pipeline.

Modern processors don’t actually execute instructions one-by-one, but maintain a *pipeline* of pending instructions so that two independent operations can be executed concurrently without waiting for each other to finish.

When I said that `add` instruction only takes one cycle, I lied a little bit. Every instruction needs a bit more than that. The whole thing takes around 5-6 clock cycles. But still, when you use it, it appears and feels like a single instruction. How does CPU achieve that?

The thing is, most of CPU isn't about computing.

![](img/pipeline.png)

Although logically it takes fundamentally 3 cycles, in CPUs it is much more.

### Latency and Throughput

![](img/superscalar.png)

and adds a new level of complexity

Programming pipelined and superscalar processors presents its own challenges, which we are going to address in this chapter.


### Instruction Scheduling

Out-of-order execution. A buffer of pending instructions.

uops, execution ports.

This is a bit of an advanced and not well understood topic.

Documentation is very obscure.

You know that your documentation is good when people have to reverse engineer it.

There are reasons to believe that folks at Intel don't know that themselves.

llvm-mca
