Chainz
======

Chainz is a lightweight library to provide chaining, functional methods to
iterables.

To install: `pip install chainz`

Basic example:
```python
from chainz import Chain

Chain(xrange(10))\
    .map(lambda x: x + 1)\
    .filter(lambda x: x % 2 == 0)\
    .omit(lambda x: x % 3 == 0)\
    .reduce(lambda x, y: x + y)
# 30
```

Chain
-----
The fundamental class in `chainz` is `Chain`, which accepts an iterable as an
argument to its constructor.  It is itself an iterable, just exposing the
supplied iterable.  It exposes functional methods like `map`,
`filter`, and `flatten`, which return the chain so as to be chainable.  These
methods alter the chain; `chain.map(f)` is the same as `chain = chain.map(f)`.

Some methods, such as `reduce` and `for_each`, are "sinks", in that they
consume the iterable.  These methods do not return the chain, to make it
clear that once they are called, the chain is done.

All non-sink methods are lazy, so they don't result in any evaluation.  Only
by using a sink method, or consuming the iterable in another way (such as
`list(chain)` or `[x for x in chain]`), do you actually evaluate the iterable.

You can think of `Chain` as a way to wrap `itertools` in a more chainable fashion.

Errors
------
By default, a `Chain` will stop whenever there's an exception.  Often that is
not what you want.  When you are processing a long list of items (something
for which `Chain` was specifically created for), you just want to note what
went wrong, and move on to the next item.  The method `on_error` allows just
that.  It takes a function `f(exception, object)` which itself takes two
parameter.  The first parameter is the raised exception.  The second parameter
is the object that caused the exception.

#### Example
```python
def handle_error(exception, obj):
  print("%s caused exception: %s" % (obj, exception))

def double(x):
  if x == 1:
    raise Exception('Bad')
  return x*2

chain = Chain(xrange(3)).on_error(handle_error).map(double)
list(chain)
# "1 caused exception: Exception('Bad')"
# [0, 2]
```

API
---
Please see the `docs/` directory for auto-generated (and thus up-to-date)
documentation.  This is generated from the doc strings, so introspection
can also be helpful (eg, `print Chain.reduce.__doc__`).
