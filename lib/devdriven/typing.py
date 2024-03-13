from typing import Any, Callable

Arity1Bool = Callable[[Any], bool]
Arity1 = Callable[[Any], Any]
Arity2 = Callable[[Any, Any], Any]
Variadic = Callable[..., Any]
VariadicBool = Callable[..., bool]
