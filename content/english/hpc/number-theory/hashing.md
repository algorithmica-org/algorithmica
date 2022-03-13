---
title: Hashing
weight: 6
draft: true
---

## Hash Functions

Hash functions take an object (a short message, document, image, or basically any binary sequence) and transform it into a fixed-length seemingly random sequence, but in a deterministic way.

Hash function is any function that is:

* Computed fast — at least in linear time, that is.
* Has a limited image — say, 64-bit values.
* "Deterministically-random:" if it takes $n$ different values, then the probability of collision of two random hashes is $\frac{1}{n}$ and can't be predicted well without knowing the hash function.

One good test is that can't create a collision in any better time than by birthday paradox. Square root of the hash space.

* Checksums.
* Hash tables. Memoisation.
* Locality-sensitive hashing

### Cryptographic

SHA-1, MD5

Passwords. There are special hash functions that have a parameter associated with it.

Salt and pepper. Dictionary attack. You can precompute a large table of hashes and just join it with a large database.

### Non-cryptographic

Identity
Polynomial
Chess

MurMurHash
CRC32

### Signatures

We now know enough to implement digital signatures.

JWT. The principle is the same as with certificates and other documents. Instead of carrying. It may or may not me encrypted.

JWT is a new piece of technology. You can essentially store whatever you need about the user on their device. Now, instead of going to a central database and checking for permisions on every request. You can also add "valid for 5 more minutes" to the token. Nobody usually even encrypts it. The simplest way you can do it is to add a fixed random string to the beginning of the message and calculating a hash of it.

### Blockchain

Proof-of-work. There are smarter blockchains that actually do something useful for proof of work.
