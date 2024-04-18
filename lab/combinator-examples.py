from typing import Any, Optional, Union, List, Tuple, Dict, Mapping, Callable, Type
from numbers import Number
from collections.abc import Collection, Sequence # , Indexable
import re
import sys
import logging

# ### SIS: _sis.repl_enabled = False

#################################################
# Combinators
#
# Combinators are functions that construct functions from other functions.

# Combinators provides a powerful mechanism for reusing logic...
# without having to anticpate the future.

#################################################

#################################################
## First-order Functions

# can be:
#   * assigned to variables
#   * passed to other functions
#   * returned as values

#################################################

def identity(x: Any) -> Any:
  'Returns the first argument.'
  return x

identity(2)
f = identity
f              # f is a function
f(2)

def plus_three(x):
  return x + 3

g = plus_three  # g is a function
g(2)

#################################################
## Second-order Functions
#################################################

# Functions with zero or more arguments that return anything.
Varadic = Callable[..., Any]

def constantly(x: Any) -> Varadic:
  'Returns a function that always returns a constant value.'
  return lambda *_args, **_kwargs: x

always_7 = constantly(7)
always_7

always_7()
always_7(11)
always_7(13, 17)

#################################################
## Predicates
#################################################

# Functions with zero or more arguments that return a boolean.
Predicate = Callable[..., bool]

def is_number(x: Any) -> bool:
  return isinstance(x, Number)

is_number(3)
not is_number(3)

is_number("hello")
not is_number("hello")

#################################################
## Predicate Combinators
#################################################

# Functions that take a Predicate and return a new Predicate.
PredicateCombinator = Callable[[Predicate], Predicate]

def not_(f: Predicate) -> Predicate:
  'Returns a function that logically negates the result of the given function.'
  return lambda *args, **kwargs: not f(*args, **kwargs)

f = not_(is_number)
f(3)
f("hello")

#################################################
## Mapping functions over sequences
#################################################

# Function with one argument that returns anything.
Uniary = Callable[[Any], Any]

def map(f: Uniary, xs: Sequence) -> Sequence:
  'Returns a sequence of `f(x)` for each element `x` in `xs`.'
  return [f(x) for x in xs]

map(identity, [1, "string", False, True, None])

map(always_7, [1, "string", False, True, None])

map(is_number, [1, "string", False, True, None])

map(not_(is_number), [1, "string", False, True, None])

map(plus_three, [3, 5, 7, 11])

#################################################
## Filtering Sequences with Predicates
#################################################

def filter(f: Uniary, xs: Sequence) -> Sequence:
  'Returns a sequence of the elements of `xs` for which `f` returns true.'
  return [x for x in xs if f(x)]

items = [1, "string", False, True, None]
filter(is_number, items)

filter(not_(is_number), items)

#################################################
## Reducing Sequences with Binary Functions
#################################################

# Functions with two arguments that return anything.
Binary = Callable[[Any, Any], Any]

def reduce(f: Binary, init: Any, xs: Sequence) -> Sequence:
  'Returns the result of `init = f(x, init)` for each element `x` in `xs`.'
  for x in xs:
    init = f(init, x)
  return init

def add(x, y):
  return x + y

reduce(add, 2, [3, 5, 7])
reduce(add, "a", ["list", 'of', 'strings'])

def conjoin(x, y):
  return (x, y)

reduce(conjoin, 2, [3, 5, 7])

# Sum of all numbers:
items = [3, "a", 5, "b", 7, "c", 11]
reduce(add, 0, filter(is_number, items))
# "Add" all non-numbers:
reduce(add, "", filter(not_(is_number), items))

#################################################
## Map is a Reduction
#################################################

def map_by_reduction(f: Uniary, xs: Sequence) -> Sequence:
  def acc(seq, x):
    return seq + [f(x)]
  return reduce(acc, [], xs)

map_by_reduction(plus_three, [3, 5, 7, 11])

#################################################
## Function Composition
#################################################

def compose(*callables) -> Varadic:
  'Returns the composition one or more functions, in reverse order.'
  'For example, `compose(g, f)(x, y)` is equivalent to `g(f(x, y))`.'
  f: Callable = callables[-1]
  gs: List[Uniary] = list(reversed(callables[:-1]))
  def h(*args, **kwargs):
    result = f(*args, **kwargs)
    for g in gs:
      result = g(result)
    return result
  return h

def multiply_by_3(x):
  return x * 3

plus_three(multiply_by_3(5))

f = compose(plus_three, multiply_by_3)
f(5)

#################################################
## Manipulating Arguments
#################################################

def reverse_args(f: Callable) -> Callable:
  def g(*args, **kwargs):
    return f(*reversed(args), **kwargs)
  return g

def divide(x, y):
  return x / y

divide(2, 3)
reverse_args(divide)(2, 3)

reduce(reverse_args(add), "a", ["list", 'of', 'strings'])
reduce(reverse_args(conjoin), 2, [3, 5, 7])

#################################################
## Partial Application
#################################################

def add_and_multiply(a, b, c):
  return (a + b) * c

add_and_multiply(2, 3, 5)

def partial(f: Callable, *args, **kwargs) -> Callable:
  def g(*args2, **kwargs2):
    return f(*(args + args2), **dict(kwargs, **kwargs2))
  return g

f = partial(add_and_multiply, 2)
f(3, 5)

#################################################
## Methods are Partially Applied Functions
#################################################

a = 2
b = 3
a + b
a.__add__(b)    # eqv. to `a + b`
f = a.__add__
f
f(3)

#################################################
## Predicators
#################################################

def re_pred(pat: str, re_func: Callable = re.search) -> Predicate:
  'Returns a predicate that matches a regular expression.'
  rx = re.compile(pat)
  return lambda x: re_func(rx, str(x)) is not None

re_pred("ab")
re_pred("ab")("abc")
re_pred("ab")("nope")

#################################################
## Binary Predicate Compositors
#################################################

def and_(f: Varadic, g: Varadic) -> Varadic:
  'Returns a function that returns `f(x, ...) and g(x, ...).'
  return lambda *args, **kwargs: f(*args, **kwargs) and g(*args, **kwargs)

def or_(f: Varadic, g: Varadic) -> Varadic:
  'Returns a function that returns `f(x, ...) or g(x, ...).'
  return lambda *args, **kwargs: f(*args, **kwargs) or g(*args, **kwargs)

def is_string(x):
  return isinstance(x, str)

is_word = and_(is_string, re_pred(r'^[a-z]+$'))
is_word("hello")
is_word("not-a-word")
is_word(2)
is_word(None)

g = or_(
  and_(is_number, plus_three),
  and_(is_string, is_word)
)
items = ["hello", "not-a-word", 2, None]
map(g, items)

#################################################
## Operator Predicates
#################################################

def binary_operator(op: str) -> Optional[Callable[[Any, Any], Any]]:
  'Returns a function for a binary operator.'
  if op in ('=='):
    return lambda a, b: a == b
  if op in ("!="):
    return lambda a, b: a != b
  if op in ("<"):
    return lambda a, b: a < b
  if op in (">"):
    return lambda a, b: a > b
  if op in ("<="):
    return lambda a, b: a <= b
  if op in (">="):
    return lambda a, b: a >= b
  else:
    return None

binary_operator("==")(2, 2)
binary_operator("!=")(2, 2)

def op_pred(op: str, b: Any) -> Optional[Predicate]:
  'Returns a predicate function given an operator name and a constant.'
  if pred := binary_operator(op):
    return lambda x: pred(x, b)
  if op in ("~=", "=~"):
    pred = re_pred(f'.*{b}.*')
    return lambda x: pred(x)
  if op in ("~!", "!~"):
    pred = re_pred(f'.*{b}.*')
    return lambda x: not pred(x)
  else:
    return None

op_pred(">", 3)

# Create predicates for a variety of operations:
operators = ['<', '==', '>']
predicates = [compose(op_pred(op, 3), int) for op in operators]
predicates
[(f, x, '=>', f(x)) for f in predicates for x in (2, 3, 5) ]

#################################################
## Sequencing
#################################################

def sequence(*functions: Sequence[Callable]) -> Callable:
  'Returns a function that calls each function in turn and returns the last result.'
  def g(*args, **kwargs):
    result = None
    for f in functions:
      result = f(result, *args, **kwargs)
    return result
  return g

#################################################
## Examples
#################################################

def modulo(modulus: int) -> Callable[[int], int]:
  return lambda x: x % modulus

mod_3 = modulo(3)
mod_3(1)
mod_3(3)
mod_3(5)


# A value `x` that supports `x[i]`:
Indexable = Union[List, Tuple, Dict]

def indexed(x: Indexable) -> Uniary:
  'Returns a function `f(i)` that returns `x[i]`.'
  return lambda i: x[i]

# Words that repeat every 3 times:
words = ['Python', 'is', 'the', 'BEST!']
f = compose(indexed(words), mod_3)
f
[f(x) for x in range(0, 10)]

#################################################
## Pattern Matching
#################################################

def is_this(y: Any) -> Predicate:
  return lambda x: x == y

def is_a(t: Type) -> Predicate:
  return lambda x: isinstance(x, t)

def is_anything() -> Predicate:
  return lambda x: True

def zero_or_more(p: Predicate) -> Predicate:
  return lambda xs: all(p(x) for x in xs)

def one_or_more(p: Predicate) -> Predicate:
  return lambda xs: len(xs) > 0 and zero_or_more(p)(xs)

def sequence_of(*predicates: Sequence[Predicate]) -> Predicate:
  def g(xs):
    if len(predicates) != len(xs):
      return False
    for p, x in zip(predicates, xs):
      if not p(x):
        return False
    return True
  return g

pattern = one_or_more(is_a(str))
pattern([])
pattern(['a'])
pattern(['a', 'b'])
pattern(['a', 2, 'b'])

pattern = sequence_of(is_a(str), is_this('b'))
pattern([])
pattern(['a'])
pattern(['a', 'b'])
pattern(['a', 'b', 'c'])
pattern([1, 2])
pattern(['a', 2])

#################################################
## Parsing Combinators
#################################################

#################################################
## Other
#################################################

def projection(key: Any, default: Any = None) -> Callable:
  'Returns a function `f(a)` that returns `a.get(key, default)`.'
  return lambda a: a.get(key, default)

### SIS: _sis.repl_enabled = True
#################################################
## Debugging Combinators
#################################################

def trace(
    f: Callable,
    name: str,
    log: Uniary,
  ) -> Callable:
  def g(*args, **kwargs):
    msg = f"{name}({format_args(args, kwargs)})"
    # log(f"{msg} => ...")
    result = f(*args, **kwargs)
    log(f"{msg} => {result!r}")
    return result
  return g

def format_args(args, kwargs):
  rep = ''
  if args:
    rep += ', '.join(map(repr, args))
  if kwargs:
    rep += ', ' + ', '.join([f'{k}={v!r}' for k, v in kwargs])
  return rep

f = compose(str, plus_three)
map(f, [2, 3, 5])

g = trace(f, "g", logging.info)
map(g, [2, 3, 5])
