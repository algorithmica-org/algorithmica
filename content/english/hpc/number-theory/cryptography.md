---
title: Cryptography
weight: 7
draft: true
---

This article is an overview of all topics related to modern internet-era cryptography.

Cryptography (from greek *kryptos* "secret" and *graphein* "to write") studies the techniques of secure communication in the presense of third (from greek graphein) parties called adversaries.

## Asymmetric Cryptography

Cryptography is mostly based on the notion that some easy to do in one way and very hard to do in reverse. One of them is integer factoring: it is easy to pick two large primes $p$ and $q$ and multiply them to produce number $n = pq$, but it is very hard to do it in reverse.

1. Pick two primes $p$ and $q$, and exponent $e$ coprime with $\phi(n) = (p - 1) \cdot (q - 1)$. Picking small exponents makes more computational sense but is slightly less secure. Usually people don't care and pick $e = 3$.
2. Calculate multiplicative inverse of $e$ modulo $\phi(n)$, that is $d \cdot e \equiv 1 \pmod \phi(n)$
3. Set $(e, n)$ as the public key and send it to everyone who wants to communicate with us. $(d, n)$ is the information necessary to decode messages.

Now, actual encoding is to calculate $c = m^e$ and decoding is to calculate $c^e = {m^e}^d = m^{ed} = m$.

To calculate $d$ and restore the message, the attacker would need to repeat step 2, that is, to restore the inverse of $e$. You would need to use extended Euclid's algorithm, but you need to feed the value of $\phi(n)$ into it, which is hard to do unless you know the factorization of $n$.

When doing actual communication, people first exchange their public keys (in any, possibly unsecure way) and then use it to encrypt messages.

This is what web browsers do when establishing connection "https." You can also do it by hand with GPG.

### Man-in-the-middle

There is an issue when establishing initial communication that the attacker could replace it and control the communication.

Between your browser and a bank. "Hey this is a message from a bank."

Trust networks. E.g., everyone can trust Google or whoever makes the device or operating system.

## Symmetric Cryptography

Disadvantage of RSA is that it is hard to calculate. You really don't want to execute 512 modulo-2^512 multiplications to decode each 64 bytes of a video that you stream from YouTube.

Such schemes exist but they require a secure key. This is where RSA comes in, but after that they switch to AES.

![](../img/aes.png)

confusion and diffusion.

Confusion means that each binary digit (bit) of the ciphertext should depend on several parts of the key, obscuring the connections between the two

Diffusion means that if we change a single bit of the plaintext, then (statistically) half of the bits in the ciphertext should change, and similarly, if we change one bit of the ciphertext, then approximately one half of the plaintext bits should change.[3] Since a bit can have only two states, when they are all re-evaluated and changed from one seemingly random position to another, half of the bits will have changed state.

The property of confusion hides the relationship between the ciphertext and the key. The idea of diffusion is to hide the relationship between the ciphertext and the plain text.

AES is implemented in hardware.

## Perfect Security

Almost all practical cryptography relies on certain assumptions. They inevitably leak at least some information about the message.

The design of cryptographic functions often relies on hardware implementation efficiency rather than math.

One-time pads can't be cracked. If someone from Russia wants to communicate with someone from the United States, they send a representative. They send a suitcase full of entropy.

Relying on not RSA not being feasibly solvable.

AES is approved by NSA for use with 196 and 256-bit keys. It's not that 128-bit keys are insecure, it's just that

Quantum computing is one of them.

[Алгоритм Шора](https://en.wikipedia.org/wiki/Shor%27s_algorithm) позволяет факторизовывать числа за полиномиальное время на квантовом компьютере. Но на 2019 год все квантовые вычисления проще симулировать на обычном компьютере. Самое большое число, факторизованное на реальном квантовом компьютере — 4088459.

### RSA

...

## Cryptographic protocols

In this article, we have learned how to:

* Transfer two messages given that you can have some random information between people.
* Transfer two messages without any common information.
* Sign a message verifying its truthfulness.
* Performing any action, although in a very computationally inefficient and non-private way.

If you feel curious, here are a few more things to think about:

* How to compare two numbers without leaking anything? For example, you may want to compare salaries with your colleagues without being fired.
* How to shuffle a card deck and play a round of poker without revealing anything?
* Private stable matching or other multi-party computations?
* Private set intersection?
* How to make it all secure when there is not one adversary, but 49%?

Cryptography is a lot more fun.

Timing information, power consumption, electromagnetic leaks or even sound can provide an extra source of information
