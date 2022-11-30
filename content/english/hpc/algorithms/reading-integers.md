---
title: Reading Decimal Integers
weight: 10
draft: true
---

I wrote a new integer parsing algorithm that is ~35x faster than scanf.

(No, this is not an April Fools' joke — although it does sound ridiculous.)

Zen 2 @ 2GHz. The compiler is Clang 13.

Ridiculous.

### Iostream

### Scanf

### Syncronization

### Getchar

### Buffering

### SIMD

http://0x80.pl/notesen/2014-10-12-parsing-decimal-numbers-part-1-swar.html


### Serial

### Transpose-based approach

### Instruction-level parallelism


### Modifications

ILP benefits would not be that huge.

One huge asterisk. We get the integers, and we can even do other parsing algorithms on them.

1.75 cycles per byte. 

AVX-512 both due to larger SIMD lane size and dedicated operations for filtering.

It accounts for ~2% of all time, but it can be optimized by using special procedures. Pad buffer with any digits.

### Future work

Next time, we will be *writing* integers.

You can create a string searcing algorithm by computing hashes in rabin-karp algorithm — although it does not seem to be possible to make an *exact* algorithm for that.

## Acknowledgements

http://0x80.pl/articles/simd-parsing-int-sequences.html

https://stackoverflow.com/questions/25622745/transpose-an-8x8-float-using-avx-avx2/25627536#25627536
