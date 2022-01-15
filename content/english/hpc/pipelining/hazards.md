---
title: Pipeline Hazards
weight: 1
---

Такая техника позволяет одновременно обрабатывать в очереди много инструкций и скрыть их задержку, но если возникает ситуация, что процессор, например, ждет данных от какой-то инструкции, либо не может заранее определить, какую инструкцию ему дальше исполнять, то в пайплайне возникает «пузырь».


by analogy with an air bubble in a fluid pipe — it propagates through the pipeline.

![Pipeline stall on the execution stage](../img/bubble.png)

Есть два основных типа пузырей: условно лёгкий, когда процессор ждет данные от предыдущей операции (зависит от задержки этой операции, но в нашем случае это ~5 циклов) и тяжелый, когда процессор ждет новых инструкций (~15 циклов).

Let's talk more about the instruction scheduling and what can go wrong in the pipeline.

situations that prevent the next instruction in the instruction stream from executing during its designated clock cycles

## Hazards

* Data hazard: waiting for an operand to be computed from a previous step
* Structural hazard: two instructions need the same part of CPU
* Control hazard: have to clear pipeline because of conditionals

Hazards create *bubbles*, or pipeline stalls

Hardware (stats-based) branch predictor is built-in in CPUs,
$\implies$ Replacing high-entropy `if`'s with predictable ones help
You can replace conditional assignments with arithmetic:
  `x = cond * a + (1 - cond) * b`
This became a common pattern, so CPU manufacturers added `CMOV` op
  that does `x = (cond ? a : b)` in one cycle
*^This masking trick will be used a lot for SIMD and CUDA later*
