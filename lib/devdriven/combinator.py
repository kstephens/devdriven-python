from typing import Any, Optional, Union, List, Callable
import re

Arity1Bool = Callable[[Any], bool]
Arity1 = Callable[[Any], Any]
Arity2 = Callable[[Any, Any], Any]
Variadic = Callable[..., Any]
VariadicBool = Callable[..., bool]

def identity(x: Any) -> Any:
  return x

def constantly(x: Any) -> Variadic:
  """
  Returns a callable that takes any number of positional and keyword arguments and always returns the value of `x`.

  Parameters:
    x (Any): The value to be returned by the callable.

  Returns:
    Callable: A callable that takes any number of positional and keyword arguments and always returns the value of `x`.
  """
  return lambda *args, **kwargs: x

def predicate(f: Variadic) -> VariadicBool:
  """
  Returns a variadic function that takes any number of arguments and keyword arguments and returns a boolean value.
  The returned function applies the given function `f` to the provided arguments and keyword arguments,
  and returns the boolean value of the result.

  Parameters:
  - `f` (Variadic): The function to be applied to the arguments and keyword arguments.

  Returns:
  - `VariadicBool`: A variadic function that takes any number of arguments and
  keyword arguments and returns a boolean value.
  """
  return lambda *args, **kwargs: (not f(*args, **kwargs)) is False

def negate(f: Variadic) -> VariadicBool:
  """
  A function that takes a callable `f` and returns a new callable that negates the result of `f`.

  Parameters:
    - f (Callable): The callable to be negated.

  Returns:
    - Callable: A new callable that negates the result of `f`.
  """
  return lambda *args, **kwargs: not f(*args, **kwargs)

def and_comp(f: Variadic, g: Variadic) -> VariadicBool:
  """
    A function that takes two callable objects, `f` and `g and returns a new callable object.
    The returned callable object takes an input `x` and any additional positional or keyword arguments.
    If `f(x)` is falsy it returns the result.
    Otherwise it returns `g(x)`.
  """
  return lambda *args, **kwargs: f(*args, **kwargs) and g(*args, **kwargs)

def or_comp(f: Variadic, g: Variadic) -> Variadic:
  """
    A function that takes two callable objects, `f` and `g`, and returns a new callable object.
    The returned callable object takes an input `x` and any additional positional or keyword arguments.
    If `f(x)` is truthy it returns the result.
    Otherwise it returns `g(x)`.
  """
  return lambda *args, **kwargs: f(*args, **kwargs) or g(*args, **kwargs)

def if_comp(f: Variadic, g: Variadic, h: Variadic) -> Variadic:
  return lambda *args, **kwargs: g(*args, **kwargs) if f(*args, **kwargs) else h(*args, **kwargs)

def is_none(f: Variadic) -> VariadicBool:
  return lambda *args, **kwargs: f(*args, **kwargs) is None

def is_not_none(f: Variadic) -> VariadicBool:
  """
  Returns a variadic function that checks if the result of applying
  the given function to the given arguments is not None.

  :param f: A callable that takes in any number of positional and keyword arguments
  and returns a value.
  :type f: Callable
  :return: A variadic function that takes in any number of positional and keyword arguments and
  returns True if the result of applying the given function to the given arguments is not None, False otherwise.
  :rtype: VariadicBool
  """
  return lambda *args, **kwargs: f(*args, **kwargs) is not None

def compose(*funcs) -> Variadic:
  """
  Composes multiple functions into a single function.

  Args:
      *funcs (Variadic): The functions to be composed.

  Returns:
      Variadic: The composed function.
  """
  return compose_each(list(funcs))

def compose_each(funcs: List[Callable]) -> Variadic:
  assert funcs
  if len(funcs) == 1:
    return funcs[0]
  if len(funcs) == 2:
    return compose_2(*funcs)
  if len(funcs) == 3:
    return compose_2(compose_arity1(funcs[0], funcs[1]), funcs[2])
  return compose_n(funcs)

def compose_n(funcs: List[Callable]) -> Variadic:
  funcs = list(funcs)
  funcs.reverse()
  g = funcs.pop(0)

  def h(*args, **kwargs):
    result = g(*args, **kwargs)
    for f in funcs:
      result = f(result)
    return result
  return h

def compose_2(g: Arity1, f: Variadic) -> Variadic:
  return lambda *args, **kwargs: g(f(*args, **kwargs))

def compose_arity1(g: Arity1, f: Arity1) -> Arity1:
  return lambda arg: g(f(arg))

def re_pred(rx_or_string: Union[re.Pattern, str]) -> Arity1Bool:
  """
  A function that takes a regular expression pattern as input and returns a predicate function.

  Parameters:
    - rx (Union[re.Pattern, str]): A re.Pattern or regular expression pattern string to be compiled.

  Returns:
    - Arity1Bool: A function that takes a string or a re.Pattern as input and
    returns True if the string matches the regular expression pattern, False otherwise.
  """
  rx: re.Pattern
  if isinstance(rx_or_string, re.Pattern):
    rx = rx_or_string
  else:
    rx = re.compile(str(rx_or_string))
  return lambda x: re.match(rx, str(x)) is not None

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
  if operator in ("~=", "=~"):
    return lambda a, b: re.match(b, a) is not None
  if operator in ("~!", "!~"):
    return lambda a, b: re.match(b, a) is None
  return None

def binary_op_const(operator: str, b: Any) -> Optional[Arity1]:
  """
  A function that takes an binary operator name with a right hand constant and returns arity-2 function.
  """
  if operator in ("~=", "=~"):
    return re_pred(f'.*{b}.*')
  if operator in ("~!", "!~"):
    pred = re_pred(f'.*{b}.*')
    return lambda a: not pred(a)
  if bop := binary_op(operator):
    return lambda a: bop(a, b)
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
