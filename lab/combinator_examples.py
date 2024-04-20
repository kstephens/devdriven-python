from typing import Any, Optional, Union, List, Tuple, Dict, Mapping, Callable, Type, Literal
from numbers import Number
from collections.abc import Collection, Sequence
import re
import sys
import logging
from pprint import pformat

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

##############################################
## Container Adapters
##############################################

# Function with one argument that returns anything.
Unary = Callable[[Any], Any]

# A value `x` that supports `x[i]`:
Indexable = Union[List, Tuple, Dict]

def at(i: Any) -> Unary:
  'Returns a function `f(x)` that returns `x[i]`.'
  return lambda x: x[i]

f = at(2)
f([0, 1, 2, 3])

g = at("a")
g({"a": 1, "b": 2})

def indexed(x: Indexable) -> Unary:
  'Returns a function `f(i)` that returns `x[i]`.'
  return lambda i: x[i]

f = indexed([0, 1, 2, 3])
f(2)

g = indexed({"a": 1, "b": 2})
g("a")

#################################################
## Predicates
#################################################

# Functions with zero or more arguments that return a boolean.
Predicate = Callable[..., bool]

def is_string(x: Any) -> bool:
  return isinstance(x, str)

is_string("hello")
not is_string("hello")

is_string(3)
not is_string(3)

#################################################
## Predicate Combinators
#################################################

# Functions that take a Predicate and return a new Predicate.
PredicateCombinator = Callable[[Predicate], Predicate]

def not_(f: Predicate) -> Predicate:
  'Returns a function that logically negates the result of the given function.'
  return lambda *args, **kwargs: not f(*args, **kwargs)

f = not_(is_string)
f("hello")
f(3)

#################################################
## Mapping functions over sequences
#################################################

def map(f: Unary, xs: Sequence) -> Sequence:
  'Returns a sequence of `f(x)` for each element `x` in `xs`.'
  return [f(x) for x in xs]

map(identity, [1, "string", False, True, None])

map(always_7, [1, "string", False, True, None])

map(is_string, [1, "string", False, True, None])

map(not_(is_string), [1, "string", False, True, None])

map(plus_three, [3, 5, 7, 11])

#################################################
## Filtering Sequences with Predicates
#################################################

def filter(f: Unary, xs: Sequence) -> Sequence:
  'Returns a sequence of the elements of `xs` for which `f` returns true.'
  return [x for x in xs if f(x)]

items = [1, "string", False, True, None]
filter(is_string, items)

filter(not_(is_string), items)

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

#######################################################

items = [3, "a", 5, "b", 7, "c", 11, True]

# Concat all strings:
reduce(add, "", filter(is_string, items))

# Sum of all numbers:
def is_number(x: Any) -> bool:
  return not isinstance(x, bool) and isinstance(x, Number)

reduce(add, 0, filter(is_number, items))

# Sum all non-strings:
reduce(add, 0, filter(not_(is_string), items))

#################################################
## Map is a Reduction
#################################################

def map_by_reduction(f: Unary, xs: Sequence) -> Sequence:
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
  gs: Sequence[Unary] = tuple(reversed(callables[:-1]))
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
## Examples
#################################################

def modulo(modulus: int) -> Callable[[int], int]:
  return lambda x: x % modulus

mod_3 = modulo(3)
mod_3(1)
mod_3(3)
mod_3(5)

# Words that repeat every 3 times:
words = ['Python', 'is', 'the', 'BEST!']
f = compose(indexed(words), mod_3)
f
[f(x) for x in range(0, 10)]

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
f(5)

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

# If x is a number add three:
f = and_(is_number, plus_three)
# If x is a string, is it a word?:
g = and_(is_string, is_word)
# One or the other:
h = or_(f, g)
items = ["hello", "not-a-word", 2, None]
map(g, items)

#################################################
## Operator Predicates
#################################################

def binary_op(op: str) -> Optional[Callable[[Any, Any], Any]]:
  'Returns a function for a binary operator.'
  return {
    '==': lambda a, b: a == b,
    '!=': lambda a, b: a != b,
    '<':  lambda a, b: a < b,
    '>':  lambda a, b: a > b,
    '<=': lambda a, b: a <= b,
    '>=': lambda a, b: a >= b,
    'and': lambda a, b: a and b,
    'or': lambda a, b: a or b,
  }.get(op)

binary_op('==') (2, 2)
binary_op('!=') (2, 2)

# Create a table `x OP y` results:
[
  f'{x} {op} {y} => {binary_op(op)(x, y)}'
  for op in ['<', '==', '>']
  for x in (2, 3, 5)
  for y in (2, 3, 5)
]

def op_pred(op: str, b: Any) -> Optional[Predicate]:
  'Returns a predicate function given an operator name and a constant.'
  if pred := binary_op(op):
    return lambda a: pred(a, b)
  if op == "not":
    return lambda a: not a
  if op == "~=":
    return re_pred(b)
  if op == "~!":
    return not_(re_pred(b))
  return None

f = op_pred(">", 3)
f(2)
f(5)


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

##############################################
## Extraction
##############################################

def reverse_apply(x: Any) -> Callable:
  return lambda f, *args, **kwargs: f(x, *args, **kwargs)

reverse_apply(1) (plus_three)

def demux(*funcs) -> Unary:
  'Return a function `h(x)` that returns `[f(x), g(x), ...].'
  return lambda x: map(reverse_apply(x), funcs)

demux(identity, len, compose(tuple, reversed))("abcd")

#################################################
## Parser Combinators
#################################################

# Parser input: a sequence of lexemes:
Input = Sequence[Any]

# A parsed value and remaining input:
Parsed = Tuple[Any, Input]

# A parser matches the input sequence and produces a result or nothing:
Parser = Callable[[Input], Optional[Parsed]]

first = at(0)
def rest(x: Input) -> Input:
  return x[1:]

def which(p: Predicate) -> Parser:
  'Returns a parser for the next lexeme when `p(lexeme)` is true.'
  def g(input: Input):
    if p(first(input)):
      return (first(input), rest(input))
  return g

g = which(is_string)
g(['a'])
g([2])
g(['a', 'b'])

#################################################
## Sequence Parsers
#################################################

ParsedSequence = Tuple[Sequence, Input]
SequenceParser = Callable[[Input], Optional[ParsedSequence]]

def one(p: Parser) -> SequenceParser:
  'Returns a parser for one lexeme in a sequence.'
  def g(input: Input):
    if input and (result := p(input)):
      parsed, input = result
      return ([parsed], input)
  return g

g = one(which(is_string))
g([])
g(['a'])
g([2])
g(['a', 'b'])

def zero_or_more(p: Parser) -> SequenceParser:
  'Returns a parser for zero or more lexemes in a sequence.'
  def g(input: Input):
    acc = []
    while input and (result := p(input)):
      parsed, input = result
      acc.append(parsed)
    return (acc, input)
  return g

g = zero_or_more(which(is_string))
g([])
g(['a'])
g([2])
g(['a', 'b'])
g(['a', 'b', 2])
g(['a', 'b', 3, 5])

def one_or_more(p: Parser) -> SequenceParser:
  'Returns a parser for one or more lexemes as a sequence.'
  p = zero_or_more(p)
  def g(input: Input):
    if (result := p(input)) and len(result[0]) >= 1:
      return result
  return g

g = one_or_more(which(is_string))
g([])
g(['a'])
g([2])
g(['a', 'b'])
g(['a', 'b', 2])
g(['a', 'b', 3, 5])

def sequence_of(*parsers) -> SequenceParser:
  'Returns a parser for parsers of a sequence.'
  def g(input: Input):
    acc = []
    for p in parsers:
      if result := p(input):
        parsed, input = result
        acc.extend(parsed)
      else:
        return None
    return (acc, input)
  return g

g = sequence_of(one(which(is_string)), one(which(is_string)))
g([])
g(['a'])
g([2])
g(['a', 'b'])
g(['a', 'b', 2])
g(['a', 'b', 3, 5])

g = sequence_of(one_or_more(which(is_number)))
g([])
g(['a'])
g([2])
g([2, 3])
g([2, 3, False])

g = sequence_of(one(which(is_string)), one_or_more(which(is_number)))
g([])
g(['a'])
g([2])
g(['a', 'b'])
g(['a', 2])
g(['a', 2, 3])
g(['a', 2, 'b', 3])
g(['a', 2, 3, False])
g(['a', 2, 3, False, 'more'])


#################################################
## Other
#################################################

def projection(key: Any, default: Any = None) -> Callable:
  'Returns a function `f(a)` that returns `a.get(key, default)`.'
  return lambda a: a.get(key, default)

#################################################
## Debugging Combinators
#################################################

def trace(
    f: Callable,
    name: str,
    log: Unary,
  ) -> Callable:
  def g(*args, **kwargs):
    msg = f"{name}({format_args(args, kwargs)})"
    # log(f"{msg} => ...")
    result = f(*args, **kwargs)
    log(f"{msg} => {result!r}")
    return result
  return g

def format_args(args, kwargs):
  return ', '.join(map(repr, args) + [f'{k}={v!r}' for k, v in kwargs])

f = compose(str, plus_three)
map(f, [2, 3, 5])

g = trace(f, "g", logging.info)
map(g, [2, 3, 5])

map_g = trace(partial(map, g), "map_g", logging.info)
map_g([2, 3, 5])

##############################################
## Mapcat
##############################################

ConcatableUnary = Callable[[Any], Sequence]

def mapcat(f: ConcatableUnary, xs: Sequence):
  'Concatenate the results of `map(f, xs)`.'
  return reduce(add, [], map(f, xs))

def duplicate(n, x):
  return [x] * n
duplicate(3, 5)

duplicate_each_3_times = partial(mapcat, partial(duplicate, 3))
duplicate_each_3_times(["a", "b"])
duplicate_each_3_times(range(4, 7))

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
