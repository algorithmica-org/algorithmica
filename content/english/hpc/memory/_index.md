---
title: Memory
weight: 4
draft: true
---

In the beginning of the [previous chapter](../analyzing-performance), I used $5 \cdot 10^8$ as a rule of thumb for how many operations can be done in a second on average. Before going into how to go above that limit, first we need to learn how not to drop below it, and #1 reason for failing is memory.

Processors can't perform instructions directly on memory-stored data. Before doing anything, CPU always needs to load the data into internal storage locations called *registers*.

How long does it take to add two numbers together? The only correct answer to this question is: it depends. Mainly on where the operands are stored.

Being one of the most widely used instructions, `add` takes only one cycle to execute. So if the data is already in registers, it takes one cycle.

If the data is in the main memory (RAM), it will take around ~20ns, or about 30-40 CPU cycles, to fetch it, and another 30-40 cycles to write it back.

And on the extreme end, the data may be stored in hard drive, which takes around 5ms, which is $10^7$ cycles.

Because of such a high variance in performance, it is very important to optimize IO operations before doing anything else. Making sure you can feed data to your CPU should almost always be the highest priority.
