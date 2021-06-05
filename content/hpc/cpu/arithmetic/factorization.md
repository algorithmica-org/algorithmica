---
title: Integer Factorization
weight: 7
---

"How big are your numbers?" determines the method to use:

- Less than 2^16 or so: Lookup table.
- Less than 2^70 or so: Richard Brent's modification of Pollard's rho algorithm.
- Less than 10^50: Lenstra elliptic curve factorization
- Less than 10^100: Quadratic Sieve
- More than 10^100: General Number Field Sieve


