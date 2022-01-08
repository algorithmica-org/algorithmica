---
title: Pipelining
weight: 3
---

When I said that `add` instruction only takes one cycle, I lied a little bit. Every instruction needs a bit more than that. The whole thing takes around 5-6 clock cycles. But still, when you use it, it appears and feels like a single instruction. How does CPU achieve that?

The thing is, most of CPU isn't about computing.

![High-resolution shot of AMD "Zen" core die](https://abload.de/img/5017e5_727ef30243c547j9kue.jpg)

As a everyday metaphor, consider how a university works. It could have one student at a time and around 50 professors, which would take turns in tutoring, but this would be highly inefficient and result in one bachelor's degree every 4 year.

Instead, universities do two smart things:

1. They teach to large groups of students at once instead of individuals.
2. They overlap their "classes" so that each can all professors keep busy. This way you can increase throughput by 4x.

For the first trick, the CPU world analogue is SIMD, which we covered in the previous chapter. And for the second, it is the technique called pipelining, which we are going to discuss next.
