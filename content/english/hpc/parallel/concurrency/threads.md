---
title: Threads
weight: 2
---

Threads are lightweight processes and threads shares with other threads their code section, data section and OS resources like open files and signals. But, like process, a thread has its own program counter (PC), a register set, and a stack space.

```cpp
#include <iostream>
using namespace std;

void print(int a[], int sz)
{
  for (int i = 0; i < sz; i++) cout << a[i] << " ";
  cout << endl;
}
 
void merge(int a[], const int low, const int mid, const int high)
{
  int *temp = new int[high-low+1];
        
  int left = low;
  int right = mid+1;
  int current = 0;
  // Merges the two arrays into temp[] 
  while(left <= mid && right <= high) {
    if(a[left] <= a[right]) {
      temp[current] = a[left];
      left++;
    }
    else { // if right element is smaller that the left
      temp[current] = a[right];  
      right++;
    }
    current++;
  }

  // Completes the array 

        // Extreme example a = 1, 2, 3 || 4, 5, 6
        // The temp array has already been filled with 1, 2, 3, 
        // So, the right side of array a will be used to fill temp.
  if(left > mid) { 
    for(int i=right; i <= high;i++) {
      temp[current] = a[i];
      current++;
    }
  }
        // Extreme example a = 6, 5, 4 || 3, 2, 1
        // The temp array has already been filled with 1, 2, 3
        // So, the left side of array a will be used to fill temp.
  else {  
    for(int i=left; i <= mid; i++) {
      temp[current] = a[i];
      current++;
    }
  }
  // into the original array
  for(int i=0; i<=high-low;i++) {
                a[i+low] = temp[i];
  }
  delete[] temp;
}
 
void merge_sort(int a[], const int low, const int high)
{
  if(low >= high) return;
  int mid = (low+high)/2;
  merge_sort(a, low, mid);  //left half
  merge_sort(a, mid+1, high);  //right half
  merge(a, low, mid, high);  //merge them
}
 
int main()
{        
  int a[] = {38, 27, 43, 3, 9, 82, 10};
  int arraySize = sizeof(a)/sizeof(int);

  print(a, arraySize);

  merge_sort(a, 0, (arraySize-1) );   

  print(a, arraySize);  
  return 0;
}
```

Threads are still managed by the operating system. They are just a more lightweight construct that can also share memory between them.

## Threads vs Processes

An important distinction is between language threads, operating system threads and hardware threads.

```python
import logging
import threading
import time

def thread_function(name):
    logging.info("Thread %s: starting", name)
    time.sleep(2)
    logging.info("Thread %s: finishing", name)

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    logging.info("Main    : before creating thread")
    x = threading.Thread(target=thread_function, args=(1,))
    logging.info("Main    : before running thread")
    x.start()
    logging.info("Main    : wait for the thread to finish")
    # x.join()
    logging.info("Main    : all done")
```

Sone languages don't support hardware threads. Python, for example, has a thing called Global Interpreter Lock, which prevents any two threads from executing at the same time. This is made to simplify concurrency. The workaround Python (and other single-threaded languages) has is to spawn processes instead:

```python
# example with processes
```
