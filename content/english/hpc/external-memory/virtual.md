---
title: Virtual Memory
weight: 2
---

Modern operating systems give every process the impression that it is working with large, contiguous sections of memory, called *virtual memory*. Physically, the memory allocated to each process may be dispersed across different areas of physical memory, or may have been moved to another storage such as SSD or HDD.

Do achieve this, the address space of the virtual memory is divided into *pages* (typically 4KB in size), and the memory system maintains a separate hardware data structure called *page table*, which points to where the data is physically stored for each page. When a process requests access to data in its memory, the operating system maps the virtual address to the physical address through the page table and forwards the read/write request to where that data is actually stored.

Since the address translation needs to be done for each memory request, this process is also cached with what's called *translation lookaside buffer* (TLB), which is just a very small cache for physical page addresses. When it doesn't hit, you essentially pay double the cost of a memory access. For this reason, some operating systems have support for larger pages (~2MB).

![From John Bell\'s OS course at University of Illinois](../img/virtual-memory.jpg)

This mechanism allows using external memory quite transparently. Operating systems have two basic mechanisms:

- *Swap files*, which let the operating system automatically use parts of an SDD or an HDD as an extension of RAM when there is not enough real RAM.
- [Memory mapping](https://en.wikipedia.org/wiki/Mmap), which lets you open a file a use its contents as if they were in the main memory.

This essentially turns your RAM into "L4 cache" for the external memory, which is a good way to reason about it.
