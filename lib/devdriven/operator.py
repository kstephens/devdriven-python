from typing import Any, Optional, Union, List, Tuple, Dict, Mapping, Callable, Type, Literal
from numbers import Number
import operator
from icecream import ic

Unary = Callable[[Any], Any]
Binary = Callable[[Any, Any], Any]

def bind_right(bop: Binary, b: Any) -> Unary:
  return lambda a: bop(a, b)

# a + (b * c)
# binary_op('+')(a, binary_op('*')(b, c))
def left_comp(f: Callable, g: Callable) -> Callable:
  def h(a, *args):
    return f(a, g(*args))
  return h

def binary_op(name: str) -> Optional[Binary]:
  'Returns a function for a binary operator by name.'
  return BINARY_OPS.get(name)

BINARY_NUMERIC_OPS = {
  '+': operator.add,
  '-': operator.sub,
  '*': operator.mul,
  '/': operator.truediv,
  '//': operator.floordiv,
  '%': operator.mod,
  '**': operator.pow,
}

BINARY_BITWISE_OPS = {
  '&': operator.and_,
  '|': operator.or_,
  '^': operator.xor,
  '>>': operator.rshift,
  '<<': operator.lshift,
}

BINARY_RELATIONAL_OPS = {
  '==': operator.eq,
  '!=': operator.ne,
  '<':  operator.lt,
  '>':  operator.gt,
  '<=': operator.le,
  '>=': operator.gt,
}

BINARY_LOGICAL_OPS = {
  'and': lambda a, b: a and b,
  'or': lambda a, b: a or b,
}

BINARY_OPS = (
  BINARY_NUMERIC_OPS |
  BINARY_BITWISE_OPS |
  BINARY_RELATIONAL_OPS |
  BINARY_LOGICAL_OPS |
  {
    'is': operator.is_,
    'is not': operator.is_not,
    '[]': operator.getitem,
  }
)


def binary_coerce(f: Binary, coerce_ops: Optional[dict] = None) -> Binary:
  'Coerces the right hand side of a binary operator.'
  coercers = coerce_ops or COERCE_BINARY_OPS
  def g(a, b):
    a_type, b_type = type(a), type(b)
    if a_type is b_type:
      return f(a, b)
    a_b = coercers
    a_b = a_b.get(a_type, a_b[None])
    a_b = a_b.get(b_type, a_b[None]) or IDENTITY_IDENTITY
    ic((f, a, b))
    a, b = a_b[0](a), a_b[1](b)
    ic((f, a, b))
    return f(a, b)
  return g

def identity(x: Any) -> Any:
  return x

IDENTITY_IDENTITY = [identity, identity]

COERCE_BINARY_OPS = {
  int: {
    float: [float, float],
    bool: [int, int],
    str: [str, str],
    None: [int, int],
  },
  float: {
    int: [float, float],
    bool: [float, float],
    str: [str, str],
    None: [float, float]
  },
  bool: {
    int: [float, float],
    bool: [float, float],
    str: [str, str],
    None: [float, float]
  },
  str: {
    None: [str, str],
  },
  None: {
    None: IDENTITY_IDENTITY,
  }
}

def int_safe(x: Any) -> Optional[int]:
  try:
    return int(x)
  except ValueError:
    return None

def float_safe(x: Any) -> Optional[float]:
  try:
    return float(x)
  except ValueError:
    return None

def number_safe(x: Any) -> Any:
  return not_none(float_safe(x)) or int_safe(x)

def str_to_bool(x: str) -> bool:
  x = x.lower()
  if x.startswith('t') or (x and x != '0'):
    return True
  if x.startswith('f') or (x and x == '0'):
    return False
  return True if x else False

COERCE_BINARY_RIGHT_NATURAL = {
  int: {
    float: [float, float],
    bool: [int, int],
    str: [int, number_safe],
    None: [int, int],
  },
  float: {
    int: [float, float],
    str: [float, number_safe],
    None: [float, float]
  },
  bool: {
    str: [bool, str_to_bool],
    None: [bool, bool],
  },
  str: {
    bool: [bool, str_to_bool],
    None: [str, str],
  },
  None: {
    None: IDENTITY_IDENTITY,
  }
}

# Helpers:

def not_none(x: Any) -> Any:
  return x if x is not None else None

def conjoin(*args) -> Tuple:
  return tuple(args)


##############################

bc = left_comp

def bop(name: str) -> Callable:
  f = binary_op(name)
  return f and binary_coerce(f, COERCE_BINARY_RIGHT_NATURAL)

ic(bop('+')(2.3, "5.7"))
ic(bc(bop('+'), bop('*'))(2.3, "5.7", 5))

