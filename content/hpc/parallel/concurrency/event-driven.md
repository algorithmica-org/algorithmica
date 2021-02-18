---
title: Event-driven Concurrency
weight: 4
---

You might have seen it in JavaScript. Such languages have event loop that constantly. They also use a single thread, because every blocking operation is mostly I/O.

```js
var callback = function() {
    console.log("Button clicked")
}

document.getElementById('someButton').addEventListener("click", callback)
```

Event-driven environments are usually single-threaded and achieve multi-threading by "sharding" requests.

## Actor Model

A more generalized approach is called the *actor model*.

It is very popular in the JVM world.

```scala
import akka.actor.Actor
import akka.actor.ActorSystem
import akka.actor.Props

class HelloActor extends Actor {
  def receive = {
    case "hello" => println("hello back at you")
    case _       => println("huh?")
  }
}

object Main extends App {
  val system = ActorSystem("HelloSystem")
  // default Actor constructor
  val helloActor = system.actorOf(Props[HelloActor], name = "helloactor")
  helloActor ! "hello"
  helloActor ! "buenos dias"
}
```

One very important advantage of using message brokers is that you can decouple communication and also move actors to another network node, enabling distributed computing.
