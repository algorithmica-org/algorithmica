---
title: Fibers
weight: 3
---

*Fibers* are lightweight threads implemented in languages itself. The way they work is they pick up. The language thus has to maintain its own runtime.

```go
package main

import (
	"fmt"
	"time"
)

func say(s string) {
	for i := 0; i < 5; i++ {
		time.Sleep(100 * time.Millisecond)
		fmt.Println(s)
	}
}

func main() {
	go say("world")
	say("hello")
}
```

The way they work is that the language maintains a group of threads ready to pick up from where they left. This is called N:M scheduling.

Similar runtimes exist for other languages, e.g., for C++ and Rust.
