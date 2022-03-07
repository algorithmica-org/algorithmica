---
title: Computer Architecture
aliases: [/hpc/analyzing-performance/assembly]
weight: 2
---

When I began learning how to optimize programs myself, one big mistake I made was to rely primarily on the empirical approach. Not understanding how computers really worked, I would semi-randomly swap nested loops, rearrange arithmetic, combine branch conditions, inline functions by hand, and follow all sorts of other performance tips I've heard from other people, blindly hoping for improvement.

Unfortunately, this is how most programmers approach optimization. Most texts about performance do not teach you to reason about software performance qualitatively. Instead they give you general advice about certain implementation approaches — and general performance intuition is clearly not enough.

It would have probably saved me dozens, if not hundreds of hours if I learned computer architecture *before* doing algorithmic programming. So, even if most people aren't *excited* about it, we are going to spend the first few chapters studying how CPUs work and start with learning assembly.
