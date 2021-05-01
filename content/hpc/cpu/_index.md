---
title: Performance Engineering
weight: 1
---

The first part covers computer architecture and optimization of single-threaded algorithms.

It walks through the main CPU optimization techniques topics such as caching, SIMD and pipelining, and provides brief examples in C++ followed by large case studies where we make a significant improvement on some STL algorithm or data structure.

Among cool things that we will speed up, in chronological order:

- 2x faster GCD (compared to `std::gcd`)
- 4x faster binary search (compared to `std::lower_bound`)
- 7x faster segment trees
- 3x faster hash tables (compared to `std::unordered_map`)
- ?x faster popcount
- 1.7x faster parsing series of integers (compared to `scanf`)
- ?x faster sorting (compared to `std::sort`)
- 2x faster sum (compared to `std::accumulate`)
- 100x faster matrix multiplication (compared to "for-for-for")

This is based on blogposts, research papers, conference talks and other work authored by a lot of people:

- Agner Fog
- Daniel Lemire
- Wojciech Muła
- Malte Skarupke
- Matt Kulukundis
- Travis Downs
- Igor Ostrovsky
- Steven Pigeon
- Denis Bakhvalov
- Kazushige Goto
- Robert van de Geijn
- Oleksandr Bacherikov
