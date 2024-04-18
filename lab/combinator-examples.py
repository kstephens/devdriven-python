from typing import Any, Optional, Tuple, Mapping, Callable, Type
from numbers import Number
from collections.abc import Collection
import re

#################################################
## Function Types
#################################################

# Functions that have zero or more arguments and return anything.
Varadic = Callable[..., Any]

# Functions that have one argument and return anything.
Uniadic = Callable[[Any], Any]

# Functions that have zero or more arguments and return a boolean.
Predicate = Callable[..., bool]

#################################################
## First-order Functions
#################################################

def identity(x: Any) -> Any:
  'Returns the first argument.'
  return x

identity(2)
f = identity
f(2)

#################################################
## Second-order Functions
#################################################

def constantly(x: Any) -> Varadic:
  'Returns a function that always returns a constant value.'
  return lambda *_args, **_kwargs: x

always_7 = constantly(7)
always_7

always_7()
always_7(11)
always_7(13, 17)

#################################################
## Simple Combinators
#################################################

def is_string(x: Any) -> bool:
  return isinstance(x, str)

is_string("hello")
is_string(3)

def negate(f: Varadic) -> Predicate:
  'Returns a function that logically negates the result of the given function.'
  return lambda *args, **kwargs: not f(*args, **kwargs)

f = negate(is_string)
f("hello")
f(3)

def not_none(f: Varadic) -> Predicate:
  'Returns a function that returns True if the given function does not return None.'
  return lambda *args, **kwargs: f(*args, **kwargs) is not None

#################################################
## Function Composition
#################################################

def compose_functions(callables: Collection[Varadic]) -> Varadic:
  'Returns a function that applies each function in `callables` to the result of the previous function.'
  def h(*args, **kwargs):
    result = f(*args, **kwargs)
    for g in callables:
      result = g(result)
    return result
  return h

def compose(*callables) -> Varadic:
  'Returns the composition one or more functions, in reverse order.'
  reverse_callables = list(callables)
  reverse_callables.reverse()
  f = reverse_callables.pop(0)
  def h(*args, **kwargs):
    result = f(*args, **kwargs)
    for g in reverse_callables:
      result = g(result)
    return result
  return h

def add_2(x):
  return x + 2

def multiply_by_3(x):
  return x * 3

add_2(multiply_by_3(5))

f = compose(add_2, multiply_by_3)
f(5)

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

add_2_and_multiply = partial(add_and_multiply, 2)
add_2_and_multiply = add_2_and_multiply(3, 5)

#################################################
## Methods are Partially Applied Functions
#################################################

(2).__add__(3)
f = (2).__add__
f
f(3)

#################################################
## Predicators
#################################################

def re_pred(pat: str, re_func: Callable = re.search) -> Predicate:
  '''
  Returns a predicate that matches the given regular expression pattern.
  '''
  rx = re.compile(pat)
  return lambda x: re_func(rx, str(x)) is not None

re_pred("ab")
re_pred("ab")("abc")
re_pred("ab")("nope")

#################################################
## Logical Compositors
#################################################

def and_(f: Varadic, g: Varadic) -> Varadic:
  """
  Returns a new function that applies `f`.
  If the result of `f` is truthy, it returns the result of `g`.
  """
  return lambda *args, **kwargs: f(*args, **kwargs) and g(*args, **kwargs)

def or_(f: Varadic, g: Varadic) -> Varadic:
  """
  Returns a new function that applies `f`.
  If the result of `f` is falsey, it returns the result of `g`.
  """
  return lambda *args, **kwargs: f(*args, **kwargs) or g(*args, **kwargs)

is_word = and_(is_string, re_pred(r'^[a-z]+$'))
is_word("hello")
is_word("not-a-word")
is_word(2)
is_word(None)

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
## Examples
#################################################

def modulo(modulus: Number) -> Callable[[Number], Number]:
  '''
  Returns a function f(x) that returns x % modulus.
  '''
  return lambda x: x % modulus

m3 = modulo(3)
m3(1)
m3(3)
m3(5)

def index_map(x: Mapping[int, Any]) -> Callable:
  '''
  Returns a function f(i) that returns x[i].
  '''
  return lambda i: x[i]

# Words that repeat every 3 times:
words = ['Python', 'is', 'the', 'BEST!']
f = compose(index_map(words), m3)
f
[f(x) for x in range(0, 10)]

#################################################
## Pattern Matching
#################################################

def is_this(x: Any) -> Predicate:
  return lambda y: x == y

def is_instanceof(t: Type) -> Predicate:
  return lambda x: isinstance(x, t)

def is_anything(x: Any) -> Predicate:
  return lambda y: True

def zero_or_more(p: Predicate) -> Predicate:
  return lambda x: all(p(y) for y in x)

def one_or_more(p: Predicate) -> Predicate:
  return lambda x: len(x) > 0 and zero_or_more(p)(x)

#################################################
## Other
#################################################

def projection(key: Any, default: Any = None) -> Callable:
  '''
  Returns a function f(a) that returns a.get(key, default).
  '''
  return lambda a: a.get(key, default)


#################################################
## Debugging combinators
#################################################

from icecream import ic

def ic_in(f: Callable) -> Callable:
  def g(*args, **kwargs):
    ic(((f, *args, kwargs), '=>'))
    return f(*args, **kwargs)
  return g

def ic_out(f: Callable) -> Callable:
  def g(*args, **kwargs):
    result = f(*args, **kwargs)
    ic(((f, *args), '=>', result))
    return result
  return g

