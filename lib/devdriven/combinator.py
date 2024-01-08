from typing import Any, List, Iterable, Callable
# from functools import reduce

def compose(*funcs) -> Callable:
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
  # !!! reduce funcs
  # raise AttributeError "too many funcs"

def compose_reduce(funcs: Iterable[Callable], result: Any) -> Any:
  for f in funcs:
    result = f(result)
  return result

def compose_2(g: Callable, f: Callable) -> Callable:
  return lambda *args, **kwargs: g(f(*args, **kwargs))

def compose_basic(g: Callable, f: Callable) -> Callable:
  return lambda arg: g(f(arg))
