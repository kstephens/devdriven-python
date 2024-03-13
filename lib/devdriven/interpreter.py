from typing import Any, Optional
import re
from .typing import Arity1, Arity2
from .combinator import re_pred

def binary_op(operator: str) -> Optional[Arity2]:
  """
  A function that takes an binary operator name and returns arity-2 function.
  """
  if operator in ("+"):
    return lambda a, b: a + b
  if operator in ("-"):
    return lambda a, b: a - b
  if operator in ("*"):
    return lambda a, b: a * b
  if operator in ("/"):
    return lambda a, b: a / b
  if operator in ("%"):
    return lambda a, b: a % b
  if operator in ('==', '='):
    return lambda a, b: a == b
  if operator in ("!="):
    return lambda a, b: a != b
  if operator in ("<"):
    return lambda a, b: a < b
  if operator in (">"):
    return lambda a, b: a > b
  if operator in ("<="):
    return lambda a, b: a <= b
  if operator in (">="):
    return lambda a, b: a >= b
  if operator in ("and"):
    return lambda a, b: a and b
  if operator in ("or"):
    return lambda a, b: a or b
  if operator in ("~=", "=~", "~"):
    return lambda a, b: re.match(b, a) is not None
  if operator in ("~!", "!~"):
    return lambda a, b: re.match(b, a) is None
  return None

def binary_op_const(operator: str, b: Any) -> Optional[Arity1]:
  """
  A function that takes an binary operator name with a right hand constant and returns arity-1 function.
  """
  if operator in ("~=", "=~", "~"):
    return re_pred(b)
  if operator in ("~!", "!~"):
    pred = re_pred(b)
    return lambda a: not pred(a)
  if bop := binary_op(operator):
    return lambda a: bop(a, b)  # type: ignore
  return None

def unary_op(operator: str) -> Optional[Arity1]:
  """
  A function that takes a unary operator name and returns arity-1 function.
  """
  if operator in ("-"):
    return lambda a: - a
  if operator in ("+"):
    return lambda a: a
  if operator in ("not"):
    return lambda a: not a
  if operator in ("abs"):
    return abs
  return None
