---
title: When to Optimize
weight: 4
draft: true
---

Why do companies like Google ask to whiteboard-solve algorithm problems in their interviews?

The reason is that organizations with more than 10000 engineers are very different from the outside world.

Sure, as you progress through career, these coding questions get replaced with complex system design problems and assessments of managerial ability. It is just irrelevant yet, because you are not getting into a senior role straight out of college.

This is mostly just my ramblings about career paths in performance engineering.

most of the CS knowledge is abstracted away by high level languages and libraries

I assume that you either want to work in the industry, or in the academia while doing something actually useful.

Algorithm design is the kind of skill that you use 20% of time, but it is responsible for 80% of success.

There are some areas where performance is a killer features. But look as Java ecosystem: it is hellishly slow, and yet it still powers most of big data ecosystem, and runs most of Android apps. Java and other VM-based languages like WebAssembly are not going away anytime soon.

Of course, there is also lot of ~~stupidity~~ bias in hiring. There are big companies that don't ask that at all, and there are companies fully comprised of either former or active competitive programmers. It makes sense, because if people believe some skill is undervalued, why will hire people with that skill, and vice versa.

In any case, the Big-O notation is not what companies really want. It is not about writing optimal problems — it's more about avoiding terribly slow ones. The ones that don't scale. Compute indeed keeps getting cheaper.

You get especially frustrated if you had a competitive programming experience. You won't get to solve these type of problems, even if they asked them on an interview. To solve them, you need other type of qualifications. Asymptotically optimal algorithm already exists, you need to optimize the constant factor. Unfortunately, only a handful of universities teach that.

## The Levels of Optimization

Programmers can be put in several "levels" in terms of their software optimization abilities:

0. *Newbie*. Those who don't think about performance at all. They usually write in high-level languages, sometimes in declarative / functional languages. Most "programmers" stay there (and there is nothing wrong with it).
1. *Undergraduate student*. Those who know about Big O notation and are familiar with basic data structures and approaches. LeetCode and CodeForces folks are there. This is also the requirement in getting into big companies — they have a lot of in-house software, large scale, and they are looking for people in the long term, so asking things like programming language.
2. *Graduate student*. Those who know that not all operations are created equal; know other cost models such as external memory model (B-tree, external sorting), word model (bitset,) or parallel computing, but still in theory.
3. *Professional developer*. Those who know actual timings of these operations. Aware that branch mispredictions are costly, memory is split into cache lines. Knows some basic SIMD techniques. 
4. *Performance engineer*. Know exactly what happens inside their hardware. Know the difference between latency and bandwidth, know about ports. Knows how to use SIMD and the rest of instruction set effectively. Can read assembly and use profilers.
5. *Intel employee*. Knows microarchitecture-specific details. This is outside of the purview of normal engineers.

In this book, we expect that the average reader is somewhere around stage 1, and hopefully by the end of it will get to 4.

You should also go through these levels when designing algorithms. First get it working in the first place, then select a bunch of reasonably asymptotically optimal algorithm. Then think about how they are going to work in terms of their memory operations or ability to execute in parallel (even if you consider single-threaded programs, there is still going to be plenty of parallelism inside a core, so this model is extremely ), and then proceed toward actual implementation. Avoid premature optimization, as Knuth once said.

---

For most web services, efficiency doesn't matter, but *latency* does.

Increasing efficiency is not how it is done nowadays.

A pageview usually generates somewhere on the order of 0.1 to 1 cent per pageview. This is a typical rate at which you monetize user attention. Say, if I simply installed AdSense, i'd be getting something like that — depending on where most of my readers are from and how many of them are using an ad blocker.

At the same time, a server with a dedicated core and 1GB of ram (which is an absurdly large amount of resources for a simple web service) costs around one millionth per second when amortized. You could fetch 100 photos with that.

Amazon had an experiment where they A/B tested their service with artificial delays and found out that a 100ms delay decreased revenue. This follows for most other services, say, you lose your "flow" at twitter, the user is likely to start thinking on something else and leave. If the delay at Google is more than a few seconds, people will just think that Google isn't working and quit.

Minimization of latency can be usually done with parallel computing, which is why distributed systems are scaled more on scalability. This part of the book is concerned with improving *efficiency* of algorithms, which makes latency lower as the by-product.

However, there are still use cases when there is a trade-off between quality and cost of servers.

- Search is hierarchical. There are usually many layers of more accurate but slower models. The more documents you rank on each layer, the better the final quality.
- Games. They are more enjoyable on large scale, but computational power also increases. This includes AI.
- AI workloads — those that have large quantities of data such as language models. Heavier models require more compute. The bottleneck in them is not the number of data, but efficiencty.

Inherently sequential algorithms, or cases when the resources are constrained. Ctrl+f'ing a large PDF is painful. Factorization.

## Estimating the impact

Sometime the optimization needs to happen in the calling layer.

SIMDJSON speeds up JSON parsing, but it may be better to not use JSON in the first place.

Protobuf or flat binary formats.

There is also a chicken and egg problem: people don't use an approach that much because it is slow and not feasible.

Cost to implement, bugs, maintainability. It is perfectly fine that most software in the world is inefficient.

What does it mean to be a better programmer? Faster programs? Faster speed of work? Fewer bugs? It is a combination of those.

Implementing compiler optimizations or databases are examples of high-leverage activities because they act as a tax on everything else — which is why you see most people writing books on these particular topics rather than software optimization in general.

---

Factorization is kind of useless by itself, but it helps with understanding how to optimize number theoretic computations in general. Same goes for sorting and binary trees: most people hold some metainformation.
