---
title: 2-SAT
weight: 9
authors:
- Sergey Slotin
- Maxim Ivanov
prerequisites:
- scc
---

**Primer.** Conjunction is the “correct” term for logical “AND” (denoted by $\wedge$ or &). Conjunction returns `true` if and only if both variables are `true`.

**Primer.** Disjunction is the “correct” term for logical “OR” (denoted by $\vee$ or |). Disjunction returns `false` if and only if both variables are `false`.

Consider the conjunction of disjunctions, that is, “AND” from “OR” of some variables or their negations. For example, such an expression:

```cpp
(a | b) & (!c | d) & (!a | !b)
```

If in letters: (A OR B) AND (NOT C OR D) AND (NOT A OR NOT B).

[It can be shown](https://ru.wikipedia.org/wiki/%D0%9A%D0%BE%D0%BD%D1%8A%D1%8E%D0%BD%D0%BA%D1%82%D0%B8%D0%B2%D0%BD%D0%B0%D1%8F_%D0%BD%D0%BE%D1%80%D0%BC%D0%B0%D0%BB%D1%8C%D0%BD%D0%B0%D1%8F_%D1%84%D0%BE%D1%80%D0%BC%D0%B0), that any logical formula can be represented in such a form.

The satisfiability (SAT) problem is to find such values of variables that the expression becomes true, or to say that there is no such set of values. For the example above, such values are `a=1, b=0, c=0, d=1` (make sure that each bracket has become `true`).

In the case of arbitrary formulas, this problem cannot be solved quickly. However, we want to solve a particular case — when we have exactly two variables in each bracket (2-SAT).

## Implication Graphs

It might seem that graphs have nothing to do with this. Note that the expression $a | b$ is equivalent to $(!a \rightarrow b) | (!b \rightarrow a)$. Here, “$\rightarrow$” means implication (“if $a$ is true, then $b$ is also true”). Using this substitution, we will transform the expression into another form — implicative.

Then we will construct the implication graph: for each variable in the graph, there will be two vertices (denoted by $x$ and $!x$), and the edges in this graph will correspond to the implications.

![](https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Implication_graph.svg/1920px-Implication_graph.svg.png)

Implication graphs are useful because if you assume that a certain expression is true, then you also need to assume that all expressions that follow from it are true, that is, those reachable in the implication graph.

Note that if for some variable $x$ it holds that $!x$ is reachable from $x$ and $x$ is reachable from $!x$, then the problem has no solution. Indeed: no matter what value we choose for the variable $x$, we will always come to a contradiction — that both the chosen value and its opposite must be chosen.

Let’s reformulate this criterion in terms of graph theory. If one vertex is reachable from another and vice versa, then these two vertices are in the same strongly connected component. Then the condition for the existence of a solution is as follows: for the 2-SAT problem to have a solution, it is necessary that for any variable $x$, vertices $x$ and $!x$ are in different strongly connected components of the implication graph.

It turns out that this condition is not only necessary but also sufficient. The algorithm described below serves as proof of this fact.

## Algorithm for Solving 2-SAT

Let the solution exist, and we need to find it. Note that for some variables, it may be the case that $!x$ is reachable from $x$ or $x$ is reachable from $!x$ (but not simultaneously). In this case, choosing one of the values of the variable $x$ will lead to a contradiction, while choosing the other will not. To choose from two values that do not lead to a contradiction, you can use the following simple rule.

**Rule.** Let $с[x]$ denote the number of the strongly connected component to which vertex $x$ belongs, where the numbers are ordered in the order of topological sorting of strongly connected components: if there is a path from $x$ to $y$, then $c[x] \leq c[y]$. Then, if $c[x] > c[!x]$, we choose the value $x$, otherwise we choose $!x$.

We will prove that with such a choice of values, we will not reach a contradiction. For definiteness, let $c[x] > c[!x]$, and therefore the vertex $x$ was chosen (the case $!x$ is proved similarly).

- We will show that $!x$ is not reachable from $x$. Since the number of the strongly connected component $c[ x ]$ is greater than the number of the component $c[ !x ]$, the connected component $x$ is located “left” of the connected component $!x$, and the latter cannot be reached from the former.
- We will show that $!y$ is not reachable from any vertex $y$ that is reachable from $x$. Let’s prove the opposite: suppose $y$ is reachable from $x$ and $!y$ is reachable from $y$. Since we obtained the implication graph by transforming $(a | b) \leftrightarrow ((!a \rightarrow b) | (!b \rightarrow a))$, and $y$ is reachable from $x$, then $!x$ is reachable from $!y$. But by the assumption, $!y$ is reachable from $y$. Then we get that $!x$ is reachable from $x$, which contradicts the condition.

It turns out that for any expression marked as true, its negation is unreachable, and likewise the negations of any expressions following from it are unreachable. Therefore, no contradictions will arise under this rule.

So, we have built an algorithm that finds the desired values of the variables under the assumption that for any variable $x$, vertices $x$ and $!x$ are in different strongly connected components:

0. We will build the implication graph by replacing all expressions of the form $a | b$ with two edges $!a \rightarrow b$ and $!b \rightarrow a$.
1. [We will find](../scc) all strongly connected components in the implication graph.
2. We will verify that for any value $x$, its negation lies in another strongly connected component: $c[ x ] \neq c[ !x ]$. If this is not the case, then there is no solution.
3. If it is necessary to output the answer, then we will set the condition $x$ to be true if $c[ x ] < c[ !x ]$, and false otherwise.
