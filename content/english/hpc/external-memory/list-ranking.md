---
title: List Ranking
weight: 5
---

Now we are going to use [external sorting](../sorting) and [joining](../sorting#joining) to solve a problem that seems useless, but is actually a very important primitive many graph algorithms in external memory as well as in parallel computing, so bear with me.

**Problem.** Given a linked list, compute *rank* of each element, equal to its distance from the front element.

![](../img/list-ranking.png)

The problem is easily solvable in RAM model, but it is nontrivial how to solve this in external memory. Since our data is stored so chaotically, we can't simply traverse the list by querying each new element. 

### Algorithm

Consider a slightly more general version of the problem. Now, each element has a *weight* $w_i$, and for each element we need to compute the sum of weights of all preceding elements instead of just its rank. To solve the initial problem, we can just set all weights equal to 1.

Now, the key idea of the algorithm is to remove some fraction of elements, recursively solve the problem, and then use it to reconstruct the answer for the initial problem.

Consider some three consecutive elements: $x$, $y$ and $z$. Assume that we deleted $y$ and solved the problem for the remaining list, which included $x$ and $z$, and now we need to restore the answer for the original triplet. The weight of $x$ would be correct as it is, but we need to calculate the answer for $y$ and adjust it for $z$, namely:

- $w_y' = w_y + w_x$
- $w_z' = w_z + w_y + w_x$

Now, we can just delete, say, first element, solve the problem recursively, and recalculate weights for the original array. But, unfortunately, it would work in quadratic time, because to make the update, we would need to know where its neighbors are, and since we can't hold the entire array in memory, we would need to scan it each time.

Therefore, on each step, we want to remove as many elements as possible. But we also have a constraint: we can't remove two consecutive elements because then merging results wouldn't be that simple.

Ideally, we want to split our list into even and odd elements, but doing this is not simpler than the initial problem. One workaround is to choose the elements at random: toss a coin for each element, and then remove all "heads" after which a "tail" follows. This way no two consecutive elements will ever be selected, and on average we get rid of ¼ of the current list. The arithmetic complexity of this solution would still be linear, because

$$
T(N) = T\left(\frac{3}{4} N\right) = O(N)
$$

The only tricky part here is how to implement the merge step in external memory. 

To do it efficiently, we need to maintain our list in the following form:
- List of tuples $(i, j)$ indicating that element $j$ follows after element $i$
- List of tuples $(i, w_i)$ indicating that element $i$ currently has weight $w_i$
- A list of deleted elements

Now, to restore the answer after randomly deleting some elements and recursively solving the smaller problem, we need to iterate over all lists using three pointers looking for deleted elements. and for each such element, we will write $(j, w_i)$ to a separate table, which would signify that before the recursive step we need to add $w_i$ to $j$. We can then join this new table with initial weights, add these additional weights to them.

After coming back from recursion, we need to update weights for the deleted elements, which we can do with the same technique, iterating over reversed connections instead of direct ones.

I/O complexity of this algorithm with therefore be the same as joining, namely $SORT(N)$.

### Applications

List ranking is especially useful in graph algorithms.

For example, we can obtain the euler tour of a tree in external memory by constructing a linked list where, for each edge, we add two copies of it, one for each direction. Then we can apply the list ranking algorithm and get the position of each node which will be the same as its number (*tin*) in the euler tour.

Exactly same approach cay be applied to parallel algorithms, but we will cover that more deeply later.
