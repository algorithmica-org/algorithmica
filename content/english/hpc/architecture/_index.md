---
title: Computer Architecture
aliases: [/hpc/analyzing-performance/assembly]
weight: 2
---

One huge mistake I made when I was learning how to write faster programs was to rely solely on the empirical approach. Not understanding how things really worked, I would semi-randomly swap nested loops, rearrange arithmetic, combine branch conditions or inline functions by hand, hoping for improvement.

Sadly, this is how an overwhelming majority of people approach optimization. Most texts about performance do not teach you to reason about performance qualitatively, but rather give you general advice about certain implementation approaches.

It would have probably saved me dozens, if not hundreds of hours if I learned computer architecture before doing algorithmic programming. So even if most people may not like it, we are going to start with the unpopular topic: reading assembly.

## Instruction Set Architectures

As software engineers, we absolutely love building and using abstractions.

Just imagine how much stuff happens when you load a URL. You type something on a keyboard; key presses are somehow detected by the OS and get sent to the browser; browser parses the URL and asks the OS to make a network request; then comes DNS, routing, TCP, HTTP and all the other OSI layers; browser parses HTML and JavaScript works its magic; some representation of a page gets sent over to GPU for rendering; image frames get sent to the monitor… and each of these steps probably involves doing dozens of more specific things in the process.

Abstractions help us in reducing all this complexity down to a single *interface* that describes what a certain module can do without fixing a concrete implementation. This provides double benefits:

- engineers working on higher-level modules only need to know the (much smaller) interface,
- engineers working on the module itself get freedom to optimize and refactor the implementation as long as it complies with its *contracts*.

Hardware engineers love abstractions too. An abstraction of a CPU is called an *instruction set architecture* (ISA), and it defines how a computer should work from a programmer's perspective. Similarly to software interfaces, it gives computer engineers the ability to improve on existing CPU designs while also giving its users — us, programmers — the confidence that things that worked before won't break on newer chips.

The ISA essentially defines how the hardware should interpret the machine language. Apart from instructions and their binary encodings, ISA importantly defines counts, sizes and purposes of registers, memory model and input/output model. Similarly to software interfaces, ISAs can be extended too: in fact, they are often updated, mostly in a backwards-compatible way, to add new and more specialized instructions that can improve performance.

### RISC vs CISC

Historically, there has been many competing ISAs in use. But unlike [character encodings and instant messaging protocols](https://xkcd.com/927/), developing and maintaining a completely separate ISA is costly, so mainstream CPUs ended up converging to one of the two families:

- **arm** chips, which are used in almost all mobile devices, as well as other computer-like devices such as TVs, smart fridges, microwaves, [car autopilots](https://en.wikipedia.org/wiki/Tesla_Autopilot) and so on. They are designed by a British company of the same name, as well as a number of electronics manufacturers including Apple and Samsung.
- **x86**[^x86] chips, which are used in almost all servers and desktops, with a few notable exceptions such as Apple's M1 MacBooks and the current [world's fastest supercomputer](https://en.wikipedia.org/wiki/Fugaku_(supercomputer)), both of which use arm-based CPUs. They are designed by a duopoly of Intel and AMD.

[^x86]: Modern 64-bit versions of x86 are known as "AMD64", "Intel 64", or by the more vendor-neutral names of "x86-64" or just "x64". A similar 64-bit extension of arm is called "AArch64" or "ARM64". In this book we will just use plain "x86" and "arm" implying the 64-bit versions.

The main difference between them is that of architectural complexity, which is more of a design philosophy rather than some strictly defined property:

- arm CPUs are *reduced* instruction set computers (RISC). They improve performance by keeping the instruction set small and highly optimized, although some less common operations have to be implemented with subroutines involving several instructions.
- x86 CPUs are *complex* instruction set computers (CISC). They improve performance by adding many specialized instructions, some of which may only be rarely used in practical programs.

The main advantages of RISC designs are manufacturing cost and power usage, so it's not surprising that the market segmented itself with arm dominating battery-powered, general-purpose devices and leaving the complex neural network and Galois field calculations to server-grade, highly-specialized x86s.
