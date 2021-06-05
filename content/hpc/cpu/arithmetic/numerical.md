---
title: Numerical Methods
weight: 2
---

### Monte Carlo Methods

### Quantization

Numerical stability is a notion in numerical analysis. An algorithm is called 'numerically stable' if an error, whatever its cause, does not grow to be much larger during the calculation

This happens if the problem is 'well-conditioned', meaning that the solution changes by only a small amount if the problem data are changed by a small amount.

In some cases, we don't need precision. In machine learning, for example, this is the whole point.

If the inputs are noisy, why shouldn't our computations be noisy too?

```c++

```

### Newton's Method

### Fast Inverse Square Root

Quake III.

Here is the original C code from [released source](https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/q_math.c#L552), including the original comment text:

```c++
float Q_rsqrt(float number) {
	long i;
	float x2, y;
	const float threehalfs = 1.5F;

	x2 = number * 0.5F;
	y  = number;
	i  = * ( long * ) &y;                       // evil floating point bit level hacking
	i  = 0x5f3759df - ( i >> 1 );               // what the fuck? 
	y  = * ( float * ) &i;
	y  = y * ( threehalfs - ( x2 * y * y ) );   // 1st iteration
//	y  = y * ( threehalfs - ( x2 * y * y ) );   // 2nd iteration, this can be removed

	return y;
}
```

With subsequent hardware advancements, especially the x86 SSE instruction `rsqrtss` that does exactly this, this method is not generally applicable to modern computing,[4] though it remains an interesting example both historically

It is heavily used in graphics, because you need to normalize vectors.

It is important from educational and historical perspective.
