#!/usr/bin/env python3.11
from typing import Any, Optional, Tuple, List, Mapping, Callable, Type
from numbers import Number
from collections.abc import Collection
import re

#################################################
## Function Types
#################################################

'''
The type of argument lists.
'''
Args = Collection[Any]

'''
The type of functions that takes zero or more arguments and returns anything.
'''
Varadic = Callable[..., Any]

'''
The type of functions that have one argument and returns anything.
'''
Uniadic = Callable[[Any], Any]

'''
The type of functions that takes zero or more arguments and returns a boolean.
'''
Predicate = Callable[..., bool]


#################################################
## Primitive Functions
#################################################

def identity(x: Any) -> Any:
  '''
  Returns the first argument.
  '''
  return x

def constantly(x: Any) -> Varadic:
  '''
  Returns a function that always returns a constant value.
  '''
  return lambda *args, **kwargs: x

#################################################
## Predicators
#################################################

def re_pred(pat: str) -> Predicate:
  '''
  Returns a predicate that matches the given regular expression pattern.
  '''
  rx = re.compile(pat)
  return lambda x: re.match(rx, str(x)) is not None

def op_pred(op: str, b: Any) -> Optional[Predicate]:
  '''
  Returns a predicate function given an operator name and a constant.
  '''
  if op in ('=='):
    return lambda x: x == b
  if op in ("!="):
    return lambda x: x != b
  if op in ("<"):
    return lambda x: x < b
  if op in (">"):
    return lambda x: x > b
  if op in ("<="):
    return lambda x: x <= b
  if op in (">="):
    return lambda x: x >= b
  if op in ("~=", "=~"):
    pred = re_pred(f'.*{b}.*')
    return lambda x: pred(x)
  if op in ("~!", "!~"):
    pred = re_pred(f'.*{b}.*')
    return lambda x: not pred(x)
  else:
    return None

#################################################
## Simple Combinators
#################################################

def negate(f: Varadic) -> Predicate:
  '''
  Returns a function that logically negates the result of the given function.
  '''
  return lambda *args, **kwargs: not f(*args, **kwargs)

def not_none(f: Varadic) -> Predicate:
  '''
  Returns a function that returns True if the given function does not return None.
  '''
  return lambda *args, **kwargs: f(*args, **kwargs) is not None

#################################################
## Compositors
#################################################

def and_compose(f: Varadic, g: Varadic) -> Varadic:
  """
  Returns a new function that applies `f`.
  If the result of `f` is truthy, it returns the result of `g`.
  """
  return lambda *args, **kwargs: f(*args, **kwargs) and g(*args, **kwargs)

def or_compose(f: Varadic, g: Varadic) -> Varadic:
  """
  Returns a new function that applies `f`.
  If the result of `f` is falsey, it returns the result of `g`.
  """
  return lambda *args, **kwargs: f(*args, **kwargs) or g(*args, **kwargs)

def compose(*callables: Tuple[Callable, ...]) -> Varadic:
  '''
  Returns the composition of more than two or more functions.
  For example, `compose(f, g, h)(x)` is equivalent to `f(g(h(x)))`.
  '''
  callables = list(callables)
  callables.reverse()
  f = callables.pop(0)

  def h(*args, **kwargs):
    result = f(*args, **kwargs)
    for g in callables:
      result = g(result)
    return result
  return h

#################################################
## Partial Application
#################################################

def partial(f: Callable, *args, **kwargs) -> Callable:
  def g(*args2, **kwargs2):
    return f(*(args + args2), **dict(kwargs, **kwargs2))
  return g

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

#################################################
## Examples
#################################################

def modulo(modulus: Number) -> Callable[[Number], Number]:
  '''
  Returns a function f(x) that returns x % modulus.
  '''
  return lambda x: x % modulus

def index_map(x: Mapping[int, Any]) -> Callable:
  '''
  Returns a function f(i) that returns x[i].
  '''
  return lambda i: x[i]

def projection(key: Any, default: Any = None) -> Callable:
  '''
  Returns a function f(a) that returns a.get(key, default).
  '''
  return lambda a: a.get(key, default)

#################################################

demo_exprs = '''
#################################################
## Primitive Functions
#################################################

identity
identity(2)

# Create a function that always returns a constant value:

constantly
always_7 := constantly(7)
always_7()
always_7(11)
always_7(13, 17)

#################################################
## More Examples
#################################################

# A function that returns a function that return the modulo of a constant number:

m3 := modulo(3)
m3(1)
m3(3)
m3(5)

# Get words that repeat every 3 times:

words := ['Python', 'is', 'the', 'BEST!']

f := compose(index_map(words), m3)

[f(x) for x in range(0, 10)]

# Create predicates for a variety of operations:

operators := ['<', '==', '>']

predicates := [compose(op_pred(op, 3), int) for op in operators]

[(f, x, '=>', f(x)) for f in predicates for x in (2, 3, 5) ]

'''
if __name__ == '__main__':
  from devdriven.showing_is_seeing import ShowingIsSeeing
  # import pprint
  # pprint.pprint(globals())
  ShowingIsSeeing(lambda : globals()).eval_exprs(demo_exprs)
