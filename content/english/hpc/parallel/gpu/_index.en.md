---
title: GPU Programming
weight: 5
---

This is an html-rendered Jupyter notebook. If you want to do the exercises right here, open it in [Colab]() or [download]() and edit it locally. In former case, you need to complete a little quest and install CUDA and PyCuda, its Python binding. On a Debian-based machine, this will probably be enough: 
* `apt-get install nvidia-cuda-dev nvidia-cuda-toolkit`
* `pip install pycuda`

Prerequisites: basic knowledge of Python and C, basic algorithms, and generally how computers work.

## Subtlties of the Moore's law

Here is a graph that roughly represents what is happening in the CPU world:

<img width='600px' src='https://www.karlrupp.net/wp-content/uploads/2015/06/35years.png'>

**Moore's law** is the observation that the number of transistors in a microprocessor doubles about every two years. This roughly means that the performance doubles too. 

You can see that around 2005 there became a shift in design .

The cores are more or less independent.

Modern GPUs appeared in early 2000s. They exploit the specific area they operate.

There are physical limitations to the speed of a core.

One solid one: the speed of light. You at least need the time for electromagnetic wave (this is light too)  to pass from one side of the motherboard to another.

Some of them have

The default free GPUs available on Google Colab are [rather powerfull](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/tesla-t4/t4-tensor-core-datasheet-951643.pdf). Author has no idea why Google does this, but this is awesome.

## Why multiprocessing?

Clock frequencies — for example, Intel Core i7 can have. This gives an upper bound

There are two types of 

## General-purpose GPU

There was a period in time when hedge funds hired computer graphics guys from game companies because of their computing skills.

There are several.

This is like with Windows and Linux.

We will stick with CUDA, because it more spread, especially in fields where noone cares, like deep learning.

## Heterogineous computing

CUDA programming involves running code on two different platforms concurrently: a host system with one or more CPUs and one or more  GPUs.

## Differences from CPUs

### Threads

Threads on a CPU are generally heavyweight entities. The operating system must swap threads on and off CPU execution channels to provide multithreading capability. Context switches are therefore slow and expensive.

By comparison, threads on GPUs are extremely lightweight. In a typical system, thousands of threads are queued up for work — in warps of 32 threads each. If the GPU must wait on one warp of threads, it simply begins executing work on another. Because separate registers are allocated to all active threads, no swapping of registers or other state need occur when switching among GPU threads. Resources stay allocated to each thread until it completes its execution.

In short, CPU cores are designed to minimize latency for one or two threads at a time each, whereas GPUs are designed to handle a large number of concurrent, lightweight threads in order to maximize throughput.

### Memory

The host system and the device each have their own distinct attached physical memories. As the host and device memories are separated by the PCI Express (PCIe) bus, items in the host memory must occasionally be communicated across the bus to the device memory or vice versa as described in What Runs on a CUDA-Enabled Device?

You can easily dump 98% of performance of you think this way.

## Installing PyCUDA

CUDA is available for many languages.

Nice documentation can be found here: https://documen.tician.de/pycuda/index.html

If you are on Colab, go to Runtime -> Change runtime type -> Hardware accelerator and set it to "GPU."


```python
# you may want to clear the output of this cell after installation
from IPython.display import clear_output
 
# this might take a while
!pip install pycuda

clear_output()
```


```python
import numpy as np

from pycuda.compiler import SourceModule
import pycuda.driver as drv
import pycuda.autoinit
```

## The basics

Let's start with a simple example and then dive deeper.

## Kernels

Just like C or C++, except that you use some custom built-in functions and specifiers.

CUDA is pretty much like normal C, except that you can specify some functions to be run as. Depending on implementation, the workflow goes as follows:

You need to think of your computer as a heterogenious machine: there is host data and device data.

* You move input data to device memory.
* You run some computation on device.
* You retrieve back this data.

In fact, kernel runs are concurrent — you program does not block until kernel run is complete. Newer devices can even run multiple kernels concurrently this way and wait for their results.

## The famous $A + B$ problem

For testing and coordination with host, we will use **NumPy** package. If you don't have it, install it: `pip install numpy`.

NumPy is a package for linear algebra and array manupulation in Python. It is written in C and is very efficient, but runs solely on CPU, so we will benchmark against it.


```python
# lets generate our test data: two float arrays filled with something random
a = numpy.random.randn(100).astype('float32')
b = numpy.random.randn(100).astype('float32')
# the type needs to be specified in this case, because randn's default type is float64, but CUDA knows nothing about it

# we need to create space where kernel should write its answers to
dest = numpy.zeros_like(a)

# this is the kernel itself
mod = SourceModule("""
    __global__ void add(float *dest, float *a, float *b) {
        const int i = threadIdx.x;
        dest[i] = a[i] + b[i];
    }
""")

# you need to specify the source code, and PyCUDA will compile it
add_kernel = mod.get_function("add")

add_kernel(
    drv.Out(dest),  # specifies that this memory should be accessible for writing
    drv.In(a),  # specifies this should be accessible for reading
    drv.In(b),
    block=(100,1,1)  # we'll talk about it in a minute
)

assert np.allclose(dest, a + b), 'WA'  # checks that these are equal
print('OK')
```


      File "<ipython-input-27-afc857479fe4>", line 19
        %%time
        ^
    SyntaxError: invalid syntax



### Memory management

In CUDA C API, you need to allocate memory explicitly. So this is actually really nice.

There is also `drv.InOut` function, which makes it available for both reading and writing, but we won't use it in this tutorial because we need to test our code too.

Most of the operations here are memory operations, so measuring performance here is useless. Don't worry, we will get to more complex examples soon enough.

GPUs have very specific operations. However, in case of NVIDIA GPUs managing it is quite simple: the cards have *compute capabilities* (1.0, 1.1, 1.2, 1.3, 2.0, etc.) and all features added at capability $x$ is also available at later versions. These can be checked at run time or compile time.

You can check differences in this Wikipedia article: https://en.wikipedia.org/wiki/CUDA#Version_features_and_specifications

## Synchronization

**Reduction** is any array-wise operation.

Assume the following problem:


## Dynamic programming

Consider the following recurrence:


```python
## Problem: dynamic programming
```

## Work vs. Latency

We actually think about both work and step complexity now.

Some tasks, especially in cryptography, cannot be parallelized. But some can.

## Summing arrays in $O(\log n)$ time

Assume we want to perform some associative (i.e., $A*(B*C) = (A*B)*C$) operation on an array of $n$ elements. Say, sum it up.

Normally, we would do that with a simple loop:

```c++
float s = 0;
for (int i = 0; i < n; i++) {
     s += a[i]; 
}
```

Its computation graphs looks like this:

<img width='400px' src='https://www.elemarjr.com/wp-content/uploads/2018/03/sequential_sum.png'>

This is optimal in terms of work complexity, but not in terms of step complexity: it's $O(n)$. We may want something that is a bit worse in terms of work complexity, but can be parallelized.

Let's try this divide-and-conquer approach:

<img width='400px' src='https://www.elemarjr.com/wp-content/uploads/2018/03/parallel_sum.png'>

Now it's still $O(n)$ work complexity (you actually need exactly the same number of additions), but this is $O(\log n)$ step complexity.

When you unroll the recursion from top to bottom, you will see that to get each required value,

<img width='400px' src='http://i.stack.imgur.com/Uehc3.png'>

## Reducing small arrays 


```python
a = numpy.random.randn(2048).astype('float32')

mod = SourceModule("""
    __global__ void sum(float *dest, float *a, float *b) {
        const int i = threadIdx.x;
        // for l from 0 to logn:
        //   __sync_threads()
        //   if the thread is active
        //     sum two elements into where they belong
        // a[0] should containt the needed sum
    }
""")

sum_kernel = mod.get_function("sum")

add_kernel(
    drv.InOut(a),
    block=(1024,1,1)
)

assert np.allclose(dest, a + b), 'WA'  # checks that these are equal
print('OK')
```

## Warps and thread blocks

Threads are bandled in groups of 32. All threads in a group must be either waiting or performing the same operation. This is caused by architectural difficulties.

<img width='300px' src='https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Block-thread.svg/1920px-Block-thread.svg.png'>

You can actually do the same stuff with 2d and 3d indexing — weird, right?

## Atomics

## Reducing big arrays

## Reducing very big arrays

Now, things get harder. It's time to tell how exactly GPU parallelism works.




```python

```

## Dense Matrix multiplication

Let's get to our first example where using GPUs actually makes sense: matrix multiplication.

## Sorting

Our last (and hardest task) is to implement sorting.

You might notice that we advocated divide-and-conquer approaches most of the time.

It's true. They work. But we can't get an algorithm that works already.


```python
# we'll use a deep learning library for benchmarking because I'm not familiar with anything else 
import torch

a = torch.randn(10**8)
b = a.cuda()
```


```python
# this should run for ~15 secs
%time c = torch.sort(a)
%time c = torch.sort(b)
```

    CPU times: user 15.2 s, sys: 177 µs, total: 15.2 s
    Wall time: 15.2 s
    CPU times: user 274 ms, sys: 237 ms, total: 511 ms
    Wall time: 511 ms


So, 30 times speedup. So, we now what we need to compete against.


```python
b.sort()
```




    (tensor([-5.4567, -5.3551, -5.3288,  ...,  5.3529,  5.4484,  5.4486],
            device='cuda:0'),
     tensor([55083205,  8383169, 73705953,  ..., 79814161, 50474932, 27805828],
            device='cuda:0'))



There are two types of sorting algorithms: data-driven.

The second can be represented and analuzed with sorting networks. Here is the one that we'll use, it's called bitonic sort.

<img src='https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/BitonicSort.svg/1686px-BitonicSort.svg.png'>

It has $O(\log n)$ stages, in total they have $1 + 2 + 3 + \ldots + \log n = O(\log^2 n$ blocks of comparisons that can't be parallelized and invonve every element of the array. So, in total it has $O(n \log^ n)$ work complexity, but $O(\log^2 n)$ step complexity, which is pretty sweet.

It is actually not that hard to implement. To make it clear, here is a slow recursive Python implementation:


```python
def bitonic_sort(a, up=False):
    if len(a) <= 1:
        return a
    else: 
        l = bitonic_sort(x[:len(a) // 2], True)
        r = bitonic_sort(x[len(a) // 2:], False)
        return bitonic_merge(first + second, up)

def bitonic_merge(a, up): 
    # assume input a is bitonic, and sorted list is returned 
    if len(a) == 1:
        return a
    else:
        bitonic_compare(a, up)
        l = bitonic_merge(a[:len(a) // 2], up)
        r = bitonic_merge(a[len(a) // 2:], up)
        return l + r

def bitonic_compare(a, up):
    dist = len(a) // 2
    for i in range(dist):  
        if (a[i] > a[i + dist]) == up:
            a[i], a[i + dist] = a[i + dist], x[i]  # this is how swap is done in Python
```


```python
bitonic_sort([57, 179, 42, 17, 300, 111])
```




    [300, 179, 111, 57, 42, 17]




```python
a = np.random.randn(10**8).astype('float32')
```


    ---------------------------------------------------------------------------

    NameError                                 Traceback (most recent call last)

    <ipython-input-27-58a927c14aae> in <module>()
    ----> 1 a = np.random.randn(10**8).astype('float32')
    

    NameError: name 'np' is not defined


## Why CUDA

Most of it still applicable.

Again, GPU programming is very specific.

SSE and tensor cores.

## Kernels

Just like C or C++, except that you use some custom built-in functions and specifiers.

CUDA is pretty much like normal C, except that you can specify some functions to be run as. Depending on implementation, the workflow goes as follows:

You need to think of your computer as a heterogenious machine: there is host data and device data.

* You move input data to device memory.
* You run some computation on device.
* You retrieve back this data.

In fact, kernel runs are concurrent — you program does not block until kernel run is complete. Newer devices can even run multiple kernels concurrently this way and wait for their results.

What you need to understand about GPUs is that they are extremely specialised for their applications.

Intrinsics for that.

Now, a lot of value comes from cryptocurrency and deep learning. The latter relies on two specific operations: matrix multiplications for linear layers and convolutions for convolutional layers used in computer vision.

First, they introduced "multiply-accumulate" operation (e.g., `x += y * z`) per 1 GPU clock cycle.

Google uses Tensor Processing Units. Nobody really knows how they work (proprietary hardware that they rent, not sell).

Each tensor core perform operations on small matrices with size 4x4. Each tensor core can perform 1 matrix multiply-accumulate operation per 1 GPU clock. It multiplies two fp16 matrices 4x4 and adds the multiplication product fp32 matrix (size: 4x4) to accumulator (that is also fp32 4x4 matrix).

This is a lot of work per 

Well, you don't really need anything more precise than that for deep learning anyway.


It is called mixed precision because input matrices are fp16 but multiplication result and accumulator are fp32 matrices.

Probably, the proper name would be "4x4 matrix cores," however NVIDIA marketing team decided to use "tensor cores."

So, see, this is not exactly fair comparison.

<img width='500px' src='https://static.seekingalpha.com/uploads/2018/8/11/275308-15340093003448672_origin.png'>

*<center>You need to extend this graph just a little bit: last November, NVIDIA's stock dropped 30% following Bitcoin crash, so I wouldn't be so hopefull</center>*

down to int4 (16-valued, you heard correct)

You need to know a lot of this specialised stuff to write efficient code. So this is a bad idea to write libraries from scratch.

Anyway, for pedagogical and recreational reasons, today we will reinvent the wheel and do a matrix multiply.

## Reducing an array

It seems to be simple: you just need to .

What actually happens when you do `s += x`? This is not a single operation. Actually, four things happen:

1. Read $x$ into register
2. Read $s$ into register
3. Calculate $s + x$
4. Write it back to wherever $s$ was initially

Two threads may execute it in an interleaved fashion. Say thread A could get $s$, but a nanosecond later thread B will be writing here, but thread A doesn't know about it and will re-write unchanged value.



Note: Atomics to do that

for small data types they are implemented on the hardware level and much more faster than that.

std::atomic is introduced to handle atomic operations in multi-thread context. In multi-thread environment, when two threads operating on the same variable, you must be extra careful to avoid race conditions. 

## Memory types

If all the various types of device memory were to race, here’s how the race would turn out:

Register size (= machine word width) is 32 bits, but they also contain 64bit capability (otherwise having more than 4gb of memory would not be possible).

* 1st place: **Register memory**
  <br> This is the data visible only to the thread that wrote it. It lasts only for the lifetime of that thread.
* 2nd place: **Shared Memory**
  <br> Shared to all threads within thread block. Lasts only for the lifetime of that block. This type of memory allows communication (data sharing) between threads. This is why you should
* 3rd place: **Constant Memory**
  <br> 
* 4th: Texture Memory
* Tie for last place: Local Memory and Global Memory

What you need to care for now is register 

For now, you need to care about differe

Accessing global memory takes hundreds.

## Problem: dense matrix multiplication

A lot of these are actually sparse. You can do stuff with social network graphs or web graphs.

Cool. But let's disapploint us for a bit:
