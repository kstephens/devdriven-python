from typing import Any, Union, List, Iterable, Callable
import re

def constantly(x: Any) -> Callable:
  """
  Returns a callable that takes any number of positional and keyword arguments and always returns the value of `x`.

  Parameters:
    x (Any): The value to be returned by the callable.

  Returns:
    Callable: A callable that takes any number of positional and keyword arguments and always returns the value of `x`.
  """
  return lambda *args, **kwargs: x

def negate(f: Callable) -> Callable:
  """
  A function that takes a callable `f` and returns a new callable that negates the result of `f`.

  Parameters:
    - f (Callable): The callable to be negated.

  Returns:
    - Callable: A new callable that negates the result of `f`.
  """
  return lambda *args, **kwargs: not f(*args, **kwargs)

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

def re_pred(rx_or_string: Union[re.Pattern, str]) -> Callable[[str], bool]:
  """
  A function that takes a regular expression pattern as input and returns a predicate function.

  Parameters:
    - rx (Union[re.Pattern, str]): A re.Pattern or regular expression pattern str to be compiled.

  Returns:
    - Callable[[str], bool]: A predicate function that takes a string as input and
    returns True if the string matches the regular expression pattern, False otherwise.
  """
  rx: re.Pattern
  if not isinstance(rx_or_string, re.Pattern):
    rx = re.compile(str(rx_or_string))
  else:
    rx = rx_or_string

  def pred(x):
    return re.match(rx, x) is not None
  return pred
