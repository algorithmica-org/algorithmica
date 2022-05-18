---
title: Probability Theory Refresher
weight: 1000
part: Appendix
draft: true
ignoreIndexing: true
---

Throughout this book, we will extensively use probability theory both to design faster algorithms and assess them. This section is a brief refresher on statistics for computer science.

It is designed to take you all the way from definitions of random variables to statistical significance and modelling without leaving any proofs behind in about 40 minutes or so.

## Basics

A **random variable** is any variable whose value depends on an outcome of a random event. It can be characterized with a set $S$ of its possible values (called *sample space*) and a function $P$ that maps them to their respective probabilities. Any function that statisfies the following properties can be a probability function:

1. The domain of $P$ is the sample space of $X$.
2. $\forall x \in X, 0 \leq P \leq 1$.
3. $\sum_{x \in X} P(x) = 1$.

For example, consider a random variable $X$ with $k$ discrete states (e.g., the result of a die toss). We can place a *uniform distribution* on $X$ — that is, make each of its states equally likely — by setting its probability distribution to:

$$
P(x=x_i) = \frac{1}{k}
$$

Random variables can be used to derive another random variables. An **event** is a subset of the sample space, and it is itself a random variable which has two states telling whether event occured or not, with the former having the same probability as the cummulative probabilities of events in its subset.

For example, the probability of rolling 4 or more on a 6-sided die is:

$$
P(x \geq 4) = \frac{|\\{ 4, 5, 6 \\}|}{|X|} = \frac{3}{6} = \frac{1}{2}
$$

A **joint probability** of two or more events is the probability of them happening at the same time. Two random variables $X$ and $Y$ are called **independent** if $p(x, y) = p(x) p(y)$ for all $x \in X$ and $y \in Y$, and **correlated** otherwise.

For example, the results of tossing one die and then tossing it again are considered independent, while a human height and body weight are. Note that correlation does not necessarily mean causation in either way.

An **observation** is a value of a random variable that was observed (that actually happened). A **sample** is a collection of independent observations of a random variable. A **statistic** is any quantity computed from the sample, such as mean or median.

The sample space of a variable does not have to be finite or even discrete, but in this case we need to adjust our definition of probability distribution. For example, when we pick a number uniformly between $0$ and $1$, each individual real-valued outcome has a probability of $0$ being picked (out of an infinite set of numbers), so instead of probability function we define *probability density*, which can be used to calculate probability of number lying in a certain range:

![](../img/pdf.png)

The probability density function should satisfy similar requirements, but in continuous case:

$$
p(a \leq x \leq b) = \int_{a}{b} p(x) \\; dx
$$

For simplicity, we will only consider finite sample spaces, but most statements can be extended to the general case.

## Expectation

The **expected value** of a random variable is intuitively the mean of large number of independent observations, and in simple finite case it is defined as the weighted average:

$$
E[X] = \sum_{i=1}^n x_i \cdot p_i = \mu
$$

For example, the expected value of a die toss is $E[X] = \sum_{i=1}^k i \cdot \frac{1}{k} = \frac{k \cdot (k + 1)}{2} \frac{1}{k} = \frac{k+1}{2} = 3.5$, which will be close to the number you would observe given a large enough sample.

Expectation is linear, meaning that $E[X+Y] = E[X] + E[Y]$ and $E[aX] = a E[X]$ if $a$ is a constant. The later property is trivial as $E[aX] = \sum a x_i p_i = a \sum a x_i p_i = a E[X]$, while the former is less obvious:

$$
\begin{aligned}
E[X+Y]  & = \sum_{x, y} (x+y) p(x, y)
\\\     & = \sum_{x, y} x p(x, y) + \sum_{x, y} y p(x, y)
\\\     & = \sum_x x p(x) \sum_y p(y) + \sum_y y p(y) \sum_x p(x)
\\\     & = \sum_x x p(x) + \sum_y y p(y)
\\\     & =  E[X] + E[Y] 
\end{aligned}
$$

This is important because it allows you to calculate means of values that can be very convoluted to derive otherwise.

### Stable Points of a Permutation

For example, consider a random permutation of lenth $n$, drawn uniformally from a set of all $n!$ possible permutations. What is the expected number of *stable points* of this permutation, that is, indices $i$ such that $p_i = i$?

Instead of going the combinatorics way and counting the number of permutations with $0$, $1$, $2$… $n$ stable points and computing the weighted sum, we can do this. Create $n$ *indicators* $I_k$ corresponding to stable points on each possible position, that is, $n$ random variables equal to $1$ if $p_i=i$ and $0$ otherwise. Then, the expected number of stable points can be expressed as:

$$
E[X]
= E[\sum_k^n I_k]
= \sum_k^n E[I_k]
= \sum_k^n P(p_i=i)
= \sum_k^n \frac{1}{n}
= \frac{n}{n}
= 1
$$

Even though the values of indicators are very much correlated (consider the case of $n=2$, where either both indicators are $1$ or none) the expected value of each of them is easy to calculate as it equals to the probability of a single corresponding event ($E[I_k] = 1 \cdot P(p_i=i) + 0 \cdot P(p_i \neq i) = P(p_i=i) = \frac{1}{n}$), and we can just sum these together due to linearity of expectation.

### Running Time of Quicksort

Quicksort is a popular algorithm for sorting a sequence of elements that works as follows:

1. Select a random element $p$ from the array (called *pivot*).
2. Partition the array into two using the predicate $a_i > p$: the first array will have all elements not exceeding $p$ and the second array will have all element larger than $p$.
3. Sort each partitioned array recursively.
4. Combine the results into a single array by concatinating the sorted arrays.

For simplicity, we will assume that all elements are distinct.

The total running time is $O(n \log n)$, but it is not outright clear why. The "array length divides on average by two each time, so the total number of steps is $O(\log n$" argument is not strong enough. Note that all 4 steps can be done in time proportional to the length of the array. Instead of analyzing what recursive functions will be, we can estimate the total number of comparisons during step 2 which will serve as the proxy for running time.

In particular, let's introduce $n^2$ indicators $I_{ij}$ equal to $1$ if we compared $i$ and $j$ at some point with $i$ as the pivot at the comparison. At some point during the execution $i$ and $j$ are going to be separated, which happens exactly when an element in the $[i, j]$ is being chosen, and on each step before that any element in that range had the same probability of being chosen. Hence, the probability of $i$ and $j$ being compared is the probability of $i$ being selected first in the $[i, j]$ range:

$$
p(i, j) = \frac{1}{|i - j| + 1}
$$

Now, to get the total running time, we need to sum all indicators accross all pairs:

$$
\sum_{i,j} I_{ij} = \sum_{i,j} p(i, j) = \sum_{i,j} \frac{1}{|i - j| + 1} \leq n \sum_{k=1}^n \frac{2}{k} = \Theta(n \log n)
$$

The last transition is true because it is a sum of harmonic series.

### Order Statistics

There is a slight modification of quicksort called quickselect that allows finding the $k$-th smallest element in $O(n)$ time, which is useful when we need to quickly compute order statistics; e.g., medians or 75-th quantiles.

1. Select a random element $p$ from the array.
2. Partition the array into two arrays $L$ and $R$ using the predicate $a_i > p$.
3. *If there are at least $k$ elemets in the first array, recursively search for $k$-th element in it, otherwise recursively search in the right array for $(k-|L|)$-th element.*

Why does it work in linear time?



### Markov's Inequality

There are a few important inequalities that are useful in getting loose by still useful upper bounds for certain quantities in probability theory — used in proofs. One of them is Markov's inequality and it states that for a nonnegative random variable $X$ and a constant $a > 0$, the probability that $X$ is at least $a$ is at most its expectation divided by $a$:

$$
P(X \geq a) \leq \frac{E[X]}{a}
$$

To prove it, consider an indicator $I_{X \geq a}$, which equals to $1$ if event $X \geq a$ occurs and $0$ if $X < a$. Then, for $a > 0$:

$$
a I_{X \geq a} \leq X
$$

This is easy to see if we consider two possible outcomes of $X \geq a$. If it holds, then $a \cdot 1 \leq X$ which was the assumption, and otherwise $a \cdot 0 \leq X$, which is true because $X$ is nonnegative.

Since this inequality holds for all values of $X$, we can take the expectation of both sides and it will not break it:

$$
E[a I_{X \geq a}] \leq E[X]
$$

The left side is the same as:

$$
E[a I_{X \geq a}] = a E[I_{X \geq a}] = a P(X \geq a)
$$

Thus we have:

$$
a P(X \geq a) \leq E[X]  \iff  P(X \geq a) \leq \frac{E[X]}{a}
$$

Markov's inequality provides some useful upper bounds. For $P(X < a)$ type of conditions, you can get a lower bound using the fact that $P(X < a) = 1 - P(X \geq a) \geq 1 - \frac{E[X]}{a}$.

### Birthday Problem

The pigeonhole principle states that if $n$ items are distributed into $m < n$ groups, then at least one group must contain more than one item.

The birthday problem consideres the case when there is enough groups for all items ($m \geq n$), but the items are distributed randomly between the groups, and concerns the probability that some pair of them will be assigned to the same group.

A concrete example is the probability that in a group of $n$ randomly chosen people, some pair of them will have the same birthday. In a group of $23$ people, there is more than 50% chance that at least two of them will share a birthday, and in a group of $70$ there is at least 99.9% chance. This result seems counterintuitive given that there are only 23 individuals and 366 days to account for, but you really need to consider that the comparisons of birthdays are made between every possible pair of individuals, so there are $23 \times 22 / 2 = 253$ pairs to consider, which is more than half the number of days in a year.

![](../img/birthday.png)

More generally, let $f(n, m)$ be the probability of *not* having a birthday collision, that is, $f(n, m) = 1 - g(n, m)$, where $g(n, m)$ is the probability of collision we actually want. Now, consider a group of $n-1$ random people with distinct birthdays and the probability that adding the $n$-th person to the group will not cause a collision, which is the same as not picking any of the $(n-1)$ already taken birthdays:

$$
f(n, m) = f(n-1,m) \cdot (1 - \frac{n-1}{m})
$$

which can be unrolled as follows:

$$
\begin{aligned}
f(n, m) &= 1 \times (1-\frac{1}{m}) \times (1-\frac{2}{m}) \times ... \times (1-\frac{n-1}{m})
\\\     &= \frac{m \times (m-1) \times (m-2) \times \ldots \times (m-n+1)}{m^n}
\\\     &= \frac{m!}{m^n (m-n)!}
\end{aligned}
$$

This product shrinks pretty quickly with $n$, but it is not clear what value of $m$ is needed to be "safe." Turns out, if $n = O(\sqrt m)$, the probability of collision tends to zero, and anything asymptotically larger guarantees a collision. One can show this with calculus, but we will choose the probability theory way.

Let's go back to the idea of counting pairs of birthdays and introduce $\frac{n \cdot (n-1)}{2}$ indicators $I_{ij}$ — one for each pair $(i, j)$ of persons — each being equal to $1$ if the birthdays match. The probability and expectation of each indicator is $\frac{1}{m}$.

Now, consider a random variable $X$ equal to the number of pairs of shared birthdays. It equals to the sum of therse indicatos, and hence its expected value is:

$$
E[X] = E[\sum_{i < j} I_{ij}] = \sum_{i < j} E[I_{ij}] = \sum_{i < j} \frac{1}{m} = \frac{n \cdot (n-1)}{2} \cdot \frac{1}{m} = \Theta(\frac{n^2}{m})
$$

This means that unless $m = \Theta(n^2)$, the number of collisions will tend to either zero or infinity. 

Formally, this doesn't mean that the probability of having at least one collision tends to $0$ or $1$, as it could be the case that we have either $0$ collisions almost always or a very large number of them almost never, leaving the average above one. To conclude the proof, we invoke the Markov's inequality:

$$
g(n, m) = P(X \geq 1) \leq \frac{E[X]}{1} = \Theta(\frac{n^2}{m})
$$

On the other side, since $P(X = 0) \leq E[X]$ (which holds for any $X \geq 0$; try to replace all $x \geq 1$ with $1$):

$$
g(n, m) = P(X \geq 1) = 1 - P(X = 0) \geq 1 - \Theta(\frac{n^2}{m})
$$

Combined, this means that $g(n, m) \to 1$ if $m \ll n^2$ and $g(n, m) \to 0$ if $m \gg n^2$.

## Variance

**Dispersion** is the extent of how "noisy" the distribution is. There are multiple ways to measure it, the most popular being the **variance**, which is the expectation of squared deviation of a random variable:

$$
Var[X] = E[(X - E[X])^2] = \sigma^2
$$

**Standard deviation**, denoted as $\sigma$ and equal to the square root of variance, is more frequently used as a practical statistic — because at least it has the same units of measurement — while the variance has some useful mathematical properties.

With a bit of algebra, we can derive a slightly more computable formula for variance:

$$
\begin{aligned}
Var(X) &= E[ (X - E[ X ])^2 ]
\\\    &= E[ X^2 - 2X E[ X ] + E[ X ]^2 ]
\\\    &= E[ X^2 ] - 2 E[ X ] E[ X ] + E[ X ]^2
\\\    &= E[ X^2 ] - E[ X ]^2
\end{aligned}
$$

The nice thing about means and variances share is that they can be added and multiplied with simple rules, which lets you easily get some useful properties of derived random variables.

In particular, if $Var(X) = \sigma^2$, the if we multiply $X$ by a constant $a$:

$$
Var(aX) = E[(aX - E[ aX ])^2] = a^2 E[ (X - E[ X ])^2] = a^2 Var(X)
$$

If we add two *independent* random variables $X$ and $Y$:

$$
\begin{aligned}
Var(X + Y) &= E[ (X+Y)^2 ] - E[X+Y]^2
\\\        &= E[ X^2 + 2XY + Y^2] - (E[X] + E[Y])^2 
\\\        &= E[X^2] + 2 E[XY] + E[Y^2] - (E[X]^2 + 2 E[X] E[Y] + E[Y]^2) 
\\\        &= E[X^2] - E[X]^2 + E[Y^2] - E[Y^2]
\\\        &= Var(X) + Var(Y)
\end{aligned}
$$

Here, we used the fact that $E[XY] = E[X] E[Y]$ for independent $X$ and $Y$, so that $2 E[XY]$ and $2 E[X] E[Y]$ cancel each other out. In general, this is not true: for example, it may so happen that $Y = -X$, and any deviation of $X$ from the mean would cancel the deviation of $Y$, making variance if $X+Y$ zero.

For correlated variables, the variance of sum is:

$$
Var(X + Y) = Var(X) + Var(Y) + 2 \cdot cov(X, Y)
$$

where $cov(X, Y)$ is the **covariance**:

$$
\begin{aligned}
cov(X, Y) &= E[(X-E[X])(Y-E[Y])]
\\\       &= E[XY] - E[X] E[Y] - E[Y] E[X] + E[X] E[Y]
\\\       &= E[XY] - E[X]E[Y]
\end{aligned}
$$

If we calculate the average of $n$ indepndent and identically distributed random variables with variance $\sigma^2$, what its variance will be? We first need to add the $n$ variables together, and after that the variance of the sum will be:

$$
Var(\sum_{i=1}^n X_i) = \sum_{i=1}^n Var(X_i) = n \sigma^2
$$

Then we, when we divide by $n$ to get the mean:

$$
Var(\frac{1}{n} \sum_{i=1}^n X_i) = \frac{1}{n^2} Var(\sum_{i=1}^n X_i) = \frac{n\sigma^2}{n^2} = \frac{\sigma^2}{n}
$$

This is called *the law of large numbers*: the variance tends to zero as $n$ grows, meaning that the mean of results of a large number of trials will converge to its expected value as more trials are performed. We will further discuss exactly what that means.

### Chebyshev's Inequality

Let $X$ be a random variable with expected value $\mu$ and variance $\sigma^2 > 0$. Then for any $k > 0$:

$$
P(|X-\mu| \geq k \sigma) \leq \frac{1}{k^2}
$$

This is called Chebyshev's inequality, and it gives upper bound on probability of value of random variable deviating from the mean by further than $k$ standard deviations. Only the case $k > 1$ is useful, and for example, it guarantees that regardless of distribution:

- 50% of results will be within $\sqrt 2 \cdot \sigma$ from the mean,
- 75% of results will be within $2 \cdot \sigma$,
- 99% of results will be within $10 \cdot \sigma$, and so on.

It follows directly from Markov's inequality when applied to random variable $(X-\mu)^2$ and $a=(k\sigma)^2$:

$$
P(|X-\mu| \geq k \sigma) = P((X-\mu)^2 \geq (k\sigma)^2) \leq \frac{E((X-\mu)^2)}{(k \sigma)^2} = \frac{\sigma^2}{k^2\sigma^2} = \frac{1}{k^2}
$$

The bound is rather loose: it is often the case that the results are much more likely to be distributed close to the mean, but it is still very useful for proofs.

### Monte Carlo Methods

Consider the following problem. You are given a map of a city  (for simplicity, assume it is just a unit square) and a list of coordinates of cell towers and their ranges. You need to calculate their coverage, that is, the share of points of the city that have at least one tower within its range.

We can rephrase the problem more concisely this way: calculate the area of intersection of a unit square and a union of circles. This problem has an exact, but very difficult solution that involves calculating all "points of interest" where any two shapes intersect and sweeping over the map from left to right and doing some complicated integration on each intersection-free segment. This solution is as precise as floating-point arithmetic can be, but slow and very painful to implement unless you are an expert in computational geometry.

What we can do instead is to pick a few points of the square at random and check each one of them if it is covered by any circle with a simple $(x-x_i)^2 + (y-y_i)^2 \leq r_i^2$ predicate. Then the ratio of covered points will be our estimate of the real answer, and the result should be pretty close given enough points.

![You can approximate $\pi$ this way if you put a single unit circle inside the square](../img/monte-carlo.gif)

But if we have a formal requirement on the precision of our answer — say, if we want 3 correct digits at least 99% of the time — how many points do we need? We can estimate the variance of our approximation and then plug it in Chebyshev's inequality.

Our estimate $X$ is the average of $n$ indicators $I_k$, each equal to $1$ if the sampled point is covered by a circle. If the covered area is $p$, then the variance of each indicator is $p \cdot (1-p) + (1 - p) \cdot p = 2 p \cdot (1 - p)$, which is at most $\frac{1}{2}$ and reaches it when $p = \frac{1}{2}$.

Since the trials are independent, the variance of the estimate is at most:

$$
Var(X) = Var(\frac{1}{n} \sum_{k=1}^n I_k) = \frac{1}{n^2} \sum_{k=1}^n Var(I_k) \leq \frac{1}{n^2} \frac{n}{2} = \frac{1}{2 \cdot n}
$$

Now, Chebyshev's inequality tells us that:

$$
P(|X-\mu| \geq k \sigma) \leq \frac{1}{k^2}
$$

which means that for a fixed acceptable error rate $\frac{1}{k^2}$ and desired bound on deviation $d = k \sigma$, the standard deviation of $X$ needs to be at most $\frac{d}{k}$. On the other side, since $Var(X) = \sigma^2 \leq \frac{1}{2 \cdot n}$, the standard deviation is bounded by $\sigma \leq \frac{1}{\sqrt{2 \cdot n}}$. Thus, we would achieve the required precision if

$$
\sigma \leq \frac{1}{\sqrt{2 \cdot n}} \leq \frac{d}{k}
$$

and solving for $n$:

$$
n \geq \frac{k^2}{2 \cdot d^2}
$$

which importantly implies that $n = \Theta(d^{-2})$. Intuitively, this means that to get $k$ decimal digits of precision ($d = 10^{-k}$), we would need $n = \Theta(10^{2k})$ trials.

These types of algorithms are called Monte-Carlo methods. There are also Las-Vegas methods, which always produce the correct result but take non-deterministic amount of time. Quicksort is an example.

## Bayes Rule

$$
P(A|B) = \frac{P(B|A)P(A)}{P(B)}
$$


### Confidence Intervals

There is a theorem slightly beyond the scope of this tutorial that states that if we continue to add distributions together, then the resulting distribution will eventually converge to what's called the normal distribution:

![](../img/clt.png)

For data with a “bell-shaped” graph, about 68% of the values lie
within one standard deviation of the mean, about 95% lie withing
two standard deviations, and over 99% lie within three standard
deviations of the mean

$$
f(x) = \frac{1}{\sigma \sqrt{2\pi} } e^{-\frac{1}{2}\left(\frac{x-\mu}{\sigma}\right)^2}
$$

What we need to know here.

### A/B Testing

Exit polls.