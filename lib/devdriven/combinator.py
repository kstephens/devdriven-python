from typing import Any, Union, List, Mapping, Iterable, Callable
import re
from .typing import Variadic, VariadicBool, Arity1, Arity1Bool


def identity(x: Any) -> Any:
    return x


def constantly(x: Any) -> Variadic:
    """
    Returns a callable that takes any number of positional and keyword arguments and always returns the value of `x`.

    Parameters:
      x (Any): The value to be returned by the callable.

    Returns:
      Callable: A callable that takes any number of positional and keyword arguments.
      @return: always returns the value of `x`.
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


def bind_arg(f: Arity1, idx: int) -> Variadic:
    return lambda *args: f(args[idx])


def bind_args(f: Variadic, idxs_: Iterable[int]) -> Variadic:
    idxs = tuple(idxs_)
    idxs_ = ()  # GC
    if len(idxs) == 0:
        return lambda *_args: f()
    if len(idxs) == 1:
        return bind_arg(f, idxs[0])

    def g(*args):
        args = [args[idx] for idx in idxs]
        return f(*args)

    return g


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
    return lambda *args, **kwargs: (
        g(*args, **kwargs) if f(*args, **kwargs) else h(*args, **kwargs)
    )


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


def get(x: Mapping[Any, Any], default: Any = None) -> Callable[[Any], Any]:
    if isinstance(x, (list, tuple)):

        def g(i):
            if i in range(0, len(x)):
                return x[i]
            return default

        return g
    return lambda i: x.get(i, default)


def re_pred(rx_or_string: Union[re.Pattern, str], re_search=re.search) -> Arity1Bool:
    """
    A function that takes a regular expression pattern as input and returns a predicate function with re.search.

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
    return lambda x: re_search(rx, str(x)) is not None
