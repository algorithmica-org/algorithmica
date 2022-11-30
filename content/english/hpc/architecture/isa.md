---
title: Instruction Set Architectures
weight: -1
---

As software engineers, we absolutely love building and using abstractions.

Just imagine how much stuff happens when you load a URL. You type something on a keyboard; key presses are somehow detected by the OS and get sent to the browser; browser parses the URL and asks the OS to make a network request; then comes DNS, routing, TCP, HTTP, and all the other OSI layers; browser parses HTML; JavaScript works its magic; some representation of a page gets sent over to GPU for rendering; image frames get sent to the monitor… and each of these steps probably involves doing dozens of more specific things in the process.

Abstractions help us in reducing all this complexity down to a single *interface* that describes what a certain *module* can do without fixing a concrete implementation. This provides double benefits:

- Engineers working on higher-level modules only need to know the (much smaller) interface.
- Engineers working on the module itself get the freedom to optimize and refactor its implementation as long as it complies with its *contracts*.

Hardware engineers love abstractions too. An abstraction of a CPU is called an *instruction set architecture* (ISA), and it defines how a computer should work from a programmer's perspective. Similar to software interfaces, it gives computer engineers the ability to improve on existing CPU designs while also giving its users — us, programmers — the confidence that things that worked before won't break on newer chips.

An ISA essentially defines how the hardware should interpret the machine language. Apart from instructions and their binary encodings, an ISA also defines the counts, sizes, and purposes of registers, the memory model, and the input/output model. Similar to software interfaces, ISAs can be extended too: in fact, they are often updated, mostly in a backward-compatible way, to add new and more specialized instructions that can improve performance.

### RISC vs CISC

Historically, there have been many competing ISAs in use. But unlike [character encodings and instant messaging protocols](https://xkcd.com/927/), developing and maintaining a completely separate ISA is costly, so mainstream CPU designs ended up converging to one of the two families:

- **Arm** chips, which are used in almost all mobile devices, as well as other computer-like devices such as TVs, smart fridges, microwaves, [car autopilots](https://en.wikipedia.org/wiki/Tesla_Autopilot), and so on. They are designed by a British company of the same name, as well as a number of electronics manufacturers including Apple and Samsung.
- **x86**[^x86] chips, which are used in almost all servers and desktops, with a few notable exceptions such as Apple's M1 MacBooks, AWS's Graviton processors, and the current [world's fastest supercomputer](https://en.wikipedia.org/wiki/Fugaku_(supercomputer)), all of which use Arm-based CPUs. They are designed by a duopoly of Intel and AMD.

[^x86]: Modern 64-bit versions of x86 are known as "AMD64," "Intel 64," or by the more vendor-neutral names of "x86-64" or just "x64." A similar 64-bit extension of Arm is called "AArch64" or "ARM64." In this book, we will just use plain "x86" and "Arm" implying the 64-bit versions.

The main difference between them is that of architectural complexity, which is more of a design philosophy rather than some strictly defined property:

- Arm CPUs are *reduced* instruction set computers (RISC). They improve performance by keeping the instruction set small and highly optimized, although some less common operations have to be implemented with subroutines involving several instructions.
- x86 CPUs are *complex* instruction set computers (CISC). They improve performance by adding many specialized instructions, some of which may only be rarely used in practical programs.

The main advantage of RISC designs is that they result in simpler and smaller chips, which projects to lower manufacturing costs and power usage. It's not surprising that the market segmented itself with Arm dominating battery-powered, general-purpose devices, and leaving the complex neural network and Galois field calculations to server-grade, highly-specialized x86s.

<!--

The two architectures are functionally similar, both sharing concepts such as pipelines, execution ports, and SIMD instructions, but since most readers are interested in optimizing applications for mainstream servers and desktops, we will mainly focus on x86 in this book.

-->
