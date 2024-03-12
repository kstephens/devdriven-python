from typing import Any, Optional, Union, List, Iterable, Callable
import re

Predicate = Callable[[Any], Any]
PredicateBool = Callable[[Any], bool]

def identity(x: Any) -> Any:
  return x

def constantly(x: Any) -> Callable:
  """
  Returns a callable that takes any number of positional and keyword arguments and always returns the value of `x`.

  Parameters:
    x (Any): The value to be returned by the callable.

  Returns:
    Callable: A callable that takes any number of positional and keyword arguments and always returns the value of `x`.
  """
  return lambda *args, **kwargs: x

def predicate(f: Callable) -> PredicateBool:
  """
  Returns a predicate function that takes any number of arguments and keyword arguments and returns a boolean value.
  The returned function applies the given function `f` to the provided arguments and keyword arguments,
  and returns the boolean value of the result.

  Parameters:
  - `f` (Callable): The function to be applied to the arguments and keyword arguments.

  Returns:
  - `PredicateBool`: A predicate function that takes any number of arguments and
  keyword arguments and returns a boolean value.
  """
  return lambda *args, **kwargs: (not f(*args, **kwargs)) is False

def negate(f: Callable) -> PredicateBool:
  """
  A function that takes a callable `f` and returns a new callable that negates the result of `f`.

  Parameters:
    - f (Callable): The callable to be negated.

  Returns:
    - Callable: A new callable that negates the result of `f`.
  """
  return lambda *args, **kwargs: not f(*args, **kwargs)

def and_comp(f: Callable, g: Callable) -> Callable:
  """
    A function that takes two callable objects, `f` and `g and returns a new callable object.
    The returned callable object takes an input `x` and any additional positional or keyword arguments.
    If `f(x)` is falsy it returns the result.
    Otherwise it returns `g(x)`.
  """
  return lambda *args, **kwargs: f(*args, **kwargs) and g(*args, **kwargs)

def or_comp(f: Callable, g: Callable) -> Callable:
  """
    A function that takes two callable objects, `f` and `g`, and returns a new callable object.
    The returned callable object takes an input `x` and any additional positional or keyword arguments.
    If `f(x)` is truthy it returns the result.
    Otherwise it returns `g(x)`.
  """
  return lambda *args, **kwargs: f(*args, **kwargs) or g(*args, **kwargs)

def if_comp(f: Callable, g: Callable, h: Callable) -> Callable:
  return lambda *args, **kwargs: g(*args, **kwargs) if f(*args, **kwargs) else h(*args, **kwargs)

def is_none(f: Callable) -> Predicate:
  return lambda *args, **kwargs: f(*args, **kwargs) is None

def is_not_none(f: Callable) -> Predicate:
  """
  Returns a predicate that checks if the result of applying the given function to the given arguments is not None.

  :param f: A callable that takes in any number of positional and keyword arguments and returns a value.
  :type f: Callable
  :return: A predicate that takes in any number of positional and keyword arguments and
  returns True if the result of applying the given function to the given arguments is not None, False otherwise.
  :rtype: Predicate
  """
  return lambda *args, **kwargs: f(*args, **kwargs) is not None

def compose(*funcs) -> Callable:
  """
  Composes multiple functions into a single function.

  Args:
      *funcs (Callable): The functions to be composed.

  Returns:
      Callable: The composed function.
  """
  return compose_each(list(funcs))

def compose_each(funcs: List[Callable]) -> Callable:
  assert funcs
  if len(funcs) == 1:
    return funcs[0]
  if len(funcs) == 2:
    return compose_2(*funcs)
  if len(funcs) == 3:
    return compose_2(compose_basic(funcs[0], funcs[1]), funcs[2])
  funcs = list(reversed(funcs))
  return lambda *args, **kwargs: compose_reduce(funcs[1:], funcs[0](*args, **kwargs))

def compose_reduce(funcs: Iterable[Callable], result: Any) -> Any:
  for f in funcs:
    result = f(result)
  return result

def compose_2(g: Callable, f: Callable) -> Callable:
  return lambda *args, **kwargs: g(f(*args, **kwargs))

def compose_basic(g: Callable, f: Callable) -> Callable:
  return lambda arg: g(f(arg))

def re_pred(rx_or_string: Union[re.Pattern, str]) -> PredicateBool:
  """
  A function that takes a regular expression pattern as input and returns a predicate function.

  Parameters:
    - rx (Union[re.Pattern, str]): A re.Pattern or regular expression pattern str to be compiled.

  Returns:
    - Callable[[str], bool]: A predicate function that takes a string as input and
    returns True if the string matches the regular expression pattern, False otherwise.
  """
  rx: re.Pattern
  if isinstance(rx_or_string, re.Pattern):
    rx = rx_or_string
  else:
    rx = re.compile(str(rx_or_string))
  return lambda x: re.match(rx, str(x)) is not None

def op_pred(f: Callable, operator: str, b: Any) -> Optional[PredicateBool]:
  if operator in ('==', '='):
    return lambda x: f(x) == b
  if operator in ("!="):
    return lambda x: f(x) != b
  if operator in ("<"):
    return lambda x: f(x) < b
  if operator in (">"):
    return lambda x: f(x) > b
  if operator in ("<="):
    return lambda x: f(x) <= b
  if operator in (">="):
    return lambda x: f(x) >= b
  if operator in ("~=", "=~"):
    pred = re_pred(f'.*{b}.*')
    return lambda x: pred(f(x))
  if operator in ("~!", "!~"):
    pred = re_pred(f'.*{b}.*')
    return lambda x: not pred(f(x))
  return None
