---
title: Optimizing Logistic Regression
weight: 5
draft: true
---

In machine learning, perhaps the most popular way of doing black-box classification is logistic regression.

Say, we want to classify $28 \times 28$ black-and-white pictures of digits into one of 10 categories (0..9):

![Numbers that some Canadian students wrote on test blanks make MNIST dataset](../img/mnist.png)

Computationally, it works like this. If we are working with $n$-dimensional data, which we need to classify into one of $m$ classes, then we multiply the input vector by a parameter matrix of size $n \times m$, and then apply a special "softmax" function to the output $m$-element vector:

$$
softmax(x)\_k = \frac{e^{x_k}}{\sum_i^m e_{x_i}}
$$

In other words, what this function does is it calculates elementwise exponent of its input vector and then normalized it so that the elements add up to 1. Since the output has $m$ positive elements that add up to 1, it can be treated as a probability distribution that the sample belongs to a certain class. We can then look at the highest probability prediction and take it as the answer of the model.

We look at a large dataset of samples and fit our parameter matrix so that we get the most answers correct. We will not go into detail about how to fit it, but once we did, we need to *inference* it, that is, to feed it new data and get predictions.

This is pretty much all that a performance engineer needs to know about machine learning. For now, we are only concerned with the computational side of things.

```c++
float w[10][28*28];
// 796 x 10
int predict(float a) {
    float s[10] = {0};

    for (int k = 0; k < 10; k++)
        for (int i = 0; i < 28*28; i++)
            s[k] += a[i] * w[k][i];

    // there is not problem with calculating exponent of small numbers,
    // but exponent of large numbers may overflow
    int mx = *std::max_element(s, s + 10);
    float sumexp = 0;
    for (int i = 0; i < 10; i++) {
        s[i] = exp(s[i] - mx);
        sumexp += s[i];
    }

    int argmax = 0;
    
    for (int i = 0; i < 10; i++) {
        s[i] /= sumexp;
        if (s[i] > s[argmax])
            argmax = i;
    }

    return argmax;
}
```

This isn't exactly worth optimizing, because that's just ~10k operations anyway, but our use case could be bigger. For example, neural networks are not fundamentally different: they just use longer chains of transformations, and not just matrix multiplication followed by a softmax.

This can also be used in a hot spot. For example, computer chess programs use similar models to determine the value of a position (the probability of winning). By the way, this is how "1-3-3-5-9" heuristic approach: you can train a logistic regression on a large dataset of chess positions that are turned into piece count differences, and that's what weights are going to look like. Score in other games works in a similar way.

The first thing we can notice is that we don't actually need to implement softmax, because we can notice that the largest logit (this is how pre-softmax numbers are called) will be largest after the softmax, so we only need to take argmax after the matrix multiplication.

Nobody in their sane mind uses C++ for training ML models.

### Quantization

Machine learning is one of the cases where we need neither range nor precision. The whole point of machine learning is to learn functions that are robust to small perturbations in data. The input data is noisy, so why our computations shouldn't be? Plus, errors should cancel each other. We can also force the matrix parameters to be in a certain range.

Using lower precision has two advantages:

1. It takes less time to fetch data.
2. We can use SIMD instructions that packs more values together.

```c++
char w[10][28*28];

int predict(char a) {
    short max = 0, argmax = 0;

    for (int k = 0; k < 10; k++) {
        short s = 0;
        for (int i = 0; i < 28*28; i++)
            s += a[i] * w[k][i];
        if (s > max)
            s = 0, argmax = k;
    }

    return argmax;
}
```
