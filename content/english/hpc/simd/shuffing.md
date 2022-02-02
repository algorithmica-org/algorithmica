---
title: In-Register Shuffles
weight: 6
---

Masking is the most widely used technique for data manipulation, but there are many other handy SIMD features that we will later use in this chapter:

- You can [broadcast](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#expand=6331,5160,588&techs=AVX,AVX2&text=broadcast) a single value to a vector from a register or a memory location.
- You can [permute](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=permute&techs=AVX,AVX2&expand=6331,5160) data inside a register almost arbitrarily.
- We can create tiny lookup tables with [pshufb](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=pshuf&techs=AVX,AVX2&expand=6331) instruction. This is useful when you have some logic that isn't implemented in SSE, and this operation is so instrumental in some algorithms that [Wojciech Muła](http://0x80.pl/) — the guy who came up with a half of the algorithms described in this chapter — took it as his [Twitter handle](https://twitter.com/pshufb)
- Since AVX2, you can use "gather" instructions that load data non-sequentially using arbitrary array indices. These don't work 8 times faster though and are usually limited by memory rather than CPU, but they are still helpful for stuff like sparse linear algebra.
- AVX512 has similar "scatter" instructions that write data non-sequentially, using either indices or [a mask](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=compress&expand=4754,4479&techs=AVX_512). You can very efficiently "filter" an array this way using a predicate.

The last two, gather and scatter, turn SIMD into proper parallel programming model, where most operations can be executed independently in terms of their memory locations. This is a huge deal: many AVX512-specific algorithms have been developed recently owning to these new instructions, and not just having twice as many SIMD lanes.

<!-- array queries with gather -->
<!-- popcnt with pshufb -->
<!-- diy filter: maskmov with permute -->
