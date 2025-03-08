# %% [markdown]
# # (Imports)

# %%
from typing import Any, Union, List, Tuple, Dict, Iterable, Mapping, Callable, Type, Literal
from numbers import Number
from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from pprint import pprint
import re
import sys
import logging
import functools
from pprint import pformat
import dis
from icecream import ic
#ic.configureOutput(includeContext=True)
map_ = map
reduce_ = functools.reduce

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# https://stackoverflow.com/a/47024809/1141958
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"

# %% [markdown]
# # One, Two, One, Two, Mic-check, ... Combinators
#
#
# This workshop is about building functions with functions.
#
# * functions as values.
# * information-hiding with functions.
# * function that create functions.
# * functions that combine functions into new functions.
# * function types.
#

# %% [markdown]
# # Function Types

# %% [markdown]
#
# Basic Types
#
# * `int` - an integer.
# * `str` - a string.
# * `List` - a list.
# * `List[T]` - a `List` containing values of `T`
# * `Any` - any type.
# * `Callable` - any thing that can be called with zero or more arguments.
# * `Callable[..., T]` - a `Callable` that returns a value of type `T`.

# %%
# Example:
# A `Callable` that has 2 parameters,
#   an `str` and `int`
#   and returns a `Tuple` of `int` and `int`:
Callable[[str, int], Tuple[int, int]]

def h(a: str, b: int) -> Tuple[int, int]:
  return (len(a), len(a) * b)

h("ab", 21)

# %% [markdown]
# # First-Order Functions

# %% [markdown]
#
# can be:
#
# * assigned to variables
# * arguments to functions.
# * returned as values.
# * have unlimited extent.

# %% [markdown]
# ## Functions don't have Names, Names have Functions

# %%
print(2)
g = print
g
g(2)

# %% [markdown]
# ## Don't know where that thing's been!

# %%
def call_func_three_times(func: Callable):
  for x in range(3):
    func(x)

call_func_three_times(print)

# %%
call_func_three_times(g)

# %% [markdown]
# ## The most useful useless function

# %%
def identity(x: Any) -> Any:
  'Returns the first argument.'
  return x

identity(2)
h = identity
h
h(3)

# %% [markdown]
# ## Anonymous Functions

# %%
lambda x: x + 3
(lambda x: x + 3)(2)           # Never had a name.

# %%
plus_three = lambda x: x + 3   # Gave it a name.
plus_three
plus_three(2)

# %% [markdown]
# # Closures

# %% [markdown]
# Functions with closure are information hiders.
# The have access to values that are otherwise not visible outside...
# They "close over variables".

# %% [markdown]
# ## Stateless Closures

# %% [markdown]
# ### Constantly return a value

# %%
def constantly(val: Any) -> Callable[[], Any]:
  return lambda : val

# %%
constantly_5 = constantly(5)
constantly_5()
constantly_5()

# %%
# Fails with arguments
try:
  constantly_5(13, 17)
except Exception as exc:
  exc

# %% [markdown]
# ### A more robust version

# %%
# Functions with zero or more arguments that return anything.
Variadic = Callable[..., Any]

def constantly(x: Any) -> Variadic:
  'Returns a function that returns a constant value.'
  return lambda *_args, **_kwargs: x

constantly_7 = constantly(7)
constantly_7
constantly_7()
constantly_7(13, 17)

# %% [markdown]
# ### Adapters

# %% [markdown]
# ### Indexable Getters

# %%
# Function with one argument that returns anything.
Unary = Callable[[Any], Any]

# A value `x` that supports `x[i]`:
Indexable = Union[List, Tuple, Dict]

# %%
def at(i: Any) -> Unary:
  'Returns a function `f(x)` that returns `x[i]`.'
  return lambda x: x[i]

a = [0, 1, 2, 3]
f = at(2)
f(a)

# %%
def indexed(x: Indexable) -> Unary:
  'Returns a function `f(i)` that returns `x[i]`.'
  return lambda i: x[i]

a = [0, 1, 2, 3]
f = indexed(a)
f(2)

# %% [markdown]
# #### Works with Strings and Dicts

# %%
s = "abcdef"
indexed("abcdef")(4)
at(3)(s)

d = {"a": 2, "b": 3}
indexed(d)("b")
at("b")(d)


# %% [markdown]
# ### Object Accessors

# %%
@dataclass
class Position:
  x: int = 0
  y: int = 0

p = Position(2, 3)
p

def getter(name: str, *default) -> Unary:
  return lambda obj: \
    getattr(obj, name, *default)

def object_get(obj):
  return lambda name, *default: \
    getattr(obj, name, *default)

g = getter('x')
g(p)

h = object_get(p)
h('x')

# %%
h('z', 999)

# %%
try:
  h('z')
except AttributeError as e:
  print(repr(e))

# %%
def setter(name: str) -> Unary:
  return lambda obj, val: setattr(obj, name, val)

def accessor(name: str) -> Callable:
  def g(obj, *val):
    if val:
      return setattr(obj, name, val[0])
    return getattr(obj, name)
  return g

# %%
s = setter('x')
s(p, 5)
p

# %%
a = accessor('x')
a(p)
a(p, 7)
p

# %% [markdown]
# ## Stateful Functions

# %% [markdown]
# ### Generators

# %%
def counter(start: int = 0, increment: int = 1) -> Callable[[], int]:
  def g() -> int:
    nonlocal start
    result = start
    start += increment
    return result
  return g

# %%
c = counter(2, 3)
c()
c()
c()

# %% [markdown]
# # Second-Order Functions

# %% [markdown]
#
# Second-Order Functions return other functions.
#
# They often have the form:
#
# ```python
# def f(a: Any, ...):
#   return lambda b: Any, ...: \
#     do_something_with(a, b)
# ```
#
# or
#
# ```python
# def f(a: Any, ...):
#   def g(b: Any, ...):  # `g` has access to `a`
#     return do_something_with(a, b)
#   return g
# ```

# %% [markdown]
# ## A Counter

# %%
Generator = Callable[[], Any]

def counter(i: int = 0) -> Generator:
  'Returns a "generator" function that returns `i`, `i + 1`, `i + 2`, ... .'
  i -= 1
  def g() -> int:
    nonlocal i
    return (i := i + 1)
  return g

c = counter(2)
c
c()
c()
c()

# %% [markdown]
# ## Combinators
#
# Combinators:
#
# * are functions that construct functions from other functions.
# * provides a powerful mechanism for reusing logic...
#   without having to anticpate the future.
#
# A combinator `c` make have the form:
#
# ```python
# def c(f: Callable, ...) -> Callable:
#   return lambda b, ...: f(do_something_with(a, b))
# ```
#
# or
#
# ```python
# def c(f: Callable, ...) -> Callable:
#   def g(b, ...):
#     return f(do_something_with(a, b))
#   return g
# ```

# %% [markdown]
# # Stateful Combinators

# %%
def with_counter(f: Callable, i: int = 0) -> Callable:
  'Returns a Callable that applies a counter to f.'
  c = counter(i)
  return lambda *args, **kwargs: \
    f(c(), *args, **kwargs)

def multiply(x, y):
  return x * y

f = with_counter(multiply, 21)
[f(2), f(2), f(3), f(5)]

# %% [markdown]
# # Predicates

# %%
# Functions with zero or more arguments that return a boolean.
Predicate = Callable[..., bool]

def is_string(x: Any) -> bool:
  'Returns true if `x` is a string.'
  return isinstance(x, str)

is_string("hello")
is_string(3)

# %% [markdown]
# # Predicate Combinators - NOT STATEFUL!

# %%
# Functions that take a Predicate and return a new Predicate.
PredicateCombinator = Callable[[Predicate], Predicate]

def not_(f: Predicate) -> Predicate:
  'Returns a function that logically negates the result of the given function.'
  return lambda *args, **kwargs: not f(*args, **kwargs)

h = not_(is_string)
h("hello")
h(3)

# %% [markdown]
# # Manipulating Sequences

# %% [markdown]
# ## Mapping functions over sequences

# %%
def map(f: Unary, xs: Sequence) -> Sequence:
  'Returns a sequence of `f(x)` for each element `x` in `xs`.'
  acc = []
  for x in xs:
    ic(x)
    acc.append(f(x))
  return acc

items = [1, "string", False, True, None]
items
map(identity, items)
map(constantly_7, items)
map(is_string, items)
map(not_(is_string), items)
map(plus_three, [3, 5, 7, 11])

# %%
map = map_

# %%
def conjoin(a, b) -> Callable[[Any, Any], Tuple[Any, Any]]:
  'Creates a Tuple from two arguments.'
  return (a, b)

dict(map(with_counter(conjoin, 21), ["a", "b", "c", "d"]))

# %% [markdown]
# ## Filtering Sequences with Predicates

# %%
def filter(f: Unary, xs: Sequence) -> Sequence:
  'Returns a sequence of the elements of `xs` for which `f` returns true.'
  return [x for x in xs if f(x)]

items = [1, "string", False, True, None]
filter(is_string, items)
filter(not_(is_string), items)

# %% [markdown]
# ## Reducing Sequences with Binary Functions

# %%
# Functions with two arguments that return anything.
Binary = Callable[[Any, Any], Any]

def reduce(f: Binary, init: Any, xs: Sequence) -> Sequence:
  'Returns the result of `init = f(x, init)` for each element `x` in `xs`.'
  for x in xs:
    init = f(init, x)
  return init

def multiply(x, y):
  return x + y

reduce(multiply, 2, [3, 5, 7])
a_list_of_strings = ["A", "List", 'Of', 'Strings']
reduce(multiply, "Here Is ", a_list_of_strings)

# %%
def conjoin(x, y):
  return (x, y)

items = [3, "a", 5, "b", 7, "c", 11, True]
reduce(conjoin, 2, items)

# %%
# Concat all strings:
reduce(multiply, "", filter(is_string, items))

# Sum of all numbers:
def is_number(x: Any) -> bool:
  return not isinstance(x, bool) and isinstance(x, Number)
reduce(multiply, 0, filter(is_number, items))

# Sum all non-strings:
reduce(multiply, 0, filter(not_(is_string), items))

# %% [markdown]
# ## Map as a Reduction

# %%
def map_r(f: Unary, xs: Sequence) -> Sequence:
  def acc(seq, x):
    return seq + [f(x)]
  return reduce(acc, [], xs)

map(plus_three, [3, 5, 7, 11])
map_r(plus_three, [3, 5, 7, 11])

# %% [markdown]
# ## Filter as a Reduction

# %%
def filter_r(f: Unary, xs: Sequence) -> Sequence:
  def acc(seq, x):
    return seq + [x] if f(x) else seq
  return reduce(acc, [], xs)

items
filter(is_string, items)
filter_r(is_string, items)

# %% [markdown]
# # Function Composition

# %%
def compose(*callables) -> Variadic:
  'Returns the composition one or more functions, in reverse order.'
  'For example, `compose(g, f)(x, y)` is equivalent to `g(f(x, y))`.'
  f: Callable = callables[-1]
  gs: Sequence[Unary] = tuple(reversed(callables[:-1]))
  def h(*args, **kwargs):
    result = f(*args, **kwargs)
    for g in gs:
      result = g(result)
    return result
  return h

def multiply_by_3(x):
  return x * 3

plus_three(multiply_by_3(5))

h = compose(plus_three, multiply_by_3)
h(5)

# %% [markdown]
# # Interlude

# %%
def modulo(modulus: int) -> Callable[[int], int]:
  return lambda x: x % modulus

mod_3 = modulo(3)
map(mod_3, range(10))

# %%
h = compose(indexed(a_list_of_strings), mod_3)
map(h, range(10))

# %% [markdown]
# # Partial Application

# %%
def add_and_multiply(a, b, c):
  return (a + b) * c

add_and_multiply(2, 3, 5)

def partial(f: Callable, *args, **kwargs) -> Callable:
  'Returns a function that prepends `args` and merges `kwargs`.'
  def g(*args2, **kwargs2):
    return f(*(args + args2), **dict(kwargs, **kwargs2))
  return g

h = partial(add_and_multiply, 2)
h(3, 5)

# %% [markdown]
# ## Methods are Partially Applied Functions

# %%
a = 2
b = 3
a + b
a.__add__(b)    # eqv. to `a + b`
h = a.__add__
h
h(7)

# %% [markdown]
# ## Arity Reduction

# %%
def unary(f: Variadic) -> Unary:
  return lambda *args, **kwargs: f((args, kwargs))

h = unary(identity)
h()
h(1)
h(1, 2)
h(a=1, b=2)

# %% [markdown]
# # Developer Affordance

# %% [markdown]
# ## Debugging

# %%
def trace(
    name: str,
    log: Unary,
    f: Callable,
  ) -> Callable:
  def g(*args, **kwargs):
    msg = f"{name}({format_args(args, kwargs)})"
    log(f"{msg} => ...")
    result = f(*args, **kwargs)
    log(f"{msg} => {result!r}")
    return result
  return g

def format_args(args, kwargs):
  return ', '.join(map(repr, args) + [f'{k}={v!r}' for k, v in kwargs])

def log(msg):
  sys.stderr.write(f'  ## {msg}\n')

h = compose(str, plus_three)
map(h, [2, 3, 5])

g = trace("g", log, h, )
map(g, [2, 3, 5])

map_g = trace("map_g", log, partial(map, g))
map_g([2, 3, 5])


# %% [markdown]
# ## Error Handlers

# %%
def except_(f: Variadic, ex_class, error: Unary) -> Callable:
  def g(*args, **kwargs):
    try:
      return f(*args, **kwargs)
    except ex_class as exc:
      return error((exc, args, kwargs))
  return g

h = except_(plus_three, TypeError, compose(partial(logging.error, 'plus_three: %s'), repr))
h(2)
h('Nope')

# %% [markdown]
# # Web Application Archecture
#
# Application middleware combinators inspired Python WSGI and Ruby Rack.
#
# An "App" is anything callable with a single dict argument:
# It receives a "Request": typically a Dict of input: headers, body and customer values passed along an "application stack".
# It returns a "Response": Tuple of HTTP status code, headers and a body (sequence of response chunks).
# Both applications and middleware follow the same protocol.
# Combinators create new Apps by wrapping others.
#

# %%
Status = int
Headers = Dict[str, Any]
Body = Iterable
Res = Tuple[Status, Headers, Body]
Req = Dict[str, Any]
App = Callable[[Req], Res]

# %% [markdown]
# ## Simple Applications

# %% [markdown]
# ### Hello, World!

# %%
def hello_world_app(req: Req) -> Res:
  return 200, {}, ("Hello, World!",)
app = hello_world_app
app({})

# %% [markdown]
# ### Do Something Useful

# %%
def something_useful_app(req: Req) -> Res:
  x, y = req['input.data']
  return 200, {}, (x * y,)

app = something_useful_app
app({'input.data': [2, 5]})

app = something_useful_app
app({'input.data': ["ab", 3]})

# %% [markdown]
# ## Application Combinators

# %% [markdown]
# Input combinators follow this pattern:

# %%
def compose_input_handler(app: App) -> App:
  def input_handler(req: Req) -> Res:
    # do something with req...
    return app(req)
  return input_handler

# %% [markdown]
# Output combinators follow this pattern:

# %%
def compose_output_handler(app: App) -> App:
  def output_handler(req: Req) -> Res:
    status, headers, body = response = app(req)  # <<<
    # do something with response...
    return status, headers, body
  return output_handler

# %% [markdown]
# ## Tracing

# %%
def trace(app: App, ident="", stream=sys.stderr) -> App:
    "Traces requests and responses."
    def indent(msg):
        stream.write(f"{'  ' * TRACE_INDENT[0]}{msg}")
    def log(msg):
        indent(f" #{msg} {ident}\n")
    def pp(data):
        indent("")
        pprint(data, stream=stream)
    def tracing(req):
        log(">>>")
        TRACE_INDENT[0] += 1
        pp(req)
        result = app(req)
        log("...")
        pp(result)
        TRACE_INDENT[0] -= 1
        log("<<<")
        return result
    return tracing
TRACE_INDENT = [0]

# %%
app = something_useful_app
app = trace(app, 'my_app')
app({'input.data': [5, 7]})

# %% [markdown]
# ### Exception Handling

# %%
def capture_exception(app: App, cls=Exception, status=500) -> App:
    def capturing_exception(req: Req) -> Res:
        try:
            return app(req)
        except cls as exc:
            return status, {"Content-Type": "text/plain"}, (repr(exc),)
    return capturing_exception

# %%
app = something_useful_app
app = capture_exception(app)
app({'input.data': [{"a": 1}, 7]})

# %% [markdown]
# ## Reading Inputs, Writing Outputs

# %%
Content = str
Data = Any

def read_input(app: App, read: Callable[[Data], Content]) -> App:
    "Reads body.stream"
    def reader(req: Req) -> Res:
        req["input.content"] = read(req["input.stream"])
        return app(req)
    return reader

# %% [markdown]
# ## Decoding Inputs, Encoding Outputs

# %%
Encoder = Callable[[Data], Content]
Decoder = Callable[[Content], Data]

def decode_content(app: App, decoder: Decoder, content_types=None, strict=False) -> App:
    """
    Decodes body with decoder(input.content) for content_types.
    If strict and Content-Type is not expected, return 400.
    """

    def decoding_content(req: Req) -> Res:
        req["input.data"] = decoder(req["input.content"])
        content_type = req.get("Content-Type")
        if strict and content_types and content_type not in content_types:
            msg = f"Unexpected Content-Type {content_type!r} : expected: {content_types!r} : "
            return 400, {"Content-Type": 'text/plain'}, (msg,)
        return app(req)
    return decoding_content


def encode_content(app: App, encoder: Encoder, content_type="text/plain") -> App:
    "Encodes body with encoder.  Sets Content-Type."
    def encoding_content(req: Req) -> Res:
        status, headers, body = app(req)
        content = "".join(map(encoder, body))
        headers |= {
            "Content-Type": content_type,
            "Content-Length": len(content),
        }
        return status, headers, [content]
    return encoding_content


# %% [markdown]
# ## Decode JSON, Encode JSON

# %%
import json

def decode_json(app: App, **kwargs) -> App:
    "Decodes JSON content."
    def decoding_json(content: Content) -> Any:
        return json.loads(content, **kwargs)
    return decode_content(app, decoding_json, content_types={'application/json', 'text/plain'}, strict=True)


def encode_json(app: App, **kwargs) -> App:
    "Encodes data as JSON."
    def encoding_json(data: Data) -> Content:
        return json.dumps(data, **kwargs) + "\n"
    return encode_content(app, encoding_json, content_type='application/json')

# %% [markdown]
# ## Simple App Handles JSON!

# %%
app = something_useful_app
# app = trace(app, 'hello_world_app')
app = decode_json(app)
# app = trace(app, 'decode_json')
app = encode_json(app)
# app = trace(app, 'encode_json')
app({'input.content': "[11, 13]", "Content-Type": 'application/json'})

# %% [markdown]
# # Logical Combinators

# %% [markdown]
# ## Predicators

# %%
def re_pred(pat: str, re_func: Callable = re.search) -> Predicate:
  'Returns a predicate that matches a regular expression.'
  rx = re.compile(pat)
  return lambda x: re_func(rx, str(x)) is not None

re_pred("ab")("abc")
re_pred("ab")("nope")

# %%
def default(f: Variadic, g: Variadic) -> Variadic:
  def h(*args, **kwargs):
    if (result := f(*args, **kwargs)) is not None:
      return result
    return g(*args, **kwargs)
  return h

# %% [markdown]
# asdf

# %% [markdown]
# ## Logical Predicate Composers

# %%
def and_(f: Variadic, g: Variadic) -> Variadic:
  'Returns a function `h(x, ...)` that returns `f(x, ...) and g(x, ...).'
  return lambda *args, **kwargs: f(*args, **kwargs) and g(*args, **kwargs)

def or_(f: Variadic, g: Variadic) -> Variadic:
  'Returns a function `h(x, ...)` that returns `f(x, ...) or g(x, ...).'
  return lambda *args, **kwargs: f(*args, **kwargs) or g(*args, **kwargs)

def is_string(x):
  return isinstance(x, str)

is_word = and_(is_string, re_pred(r'^[a-z]+$'))
is_word("hello")
is_word("not-a-word")
is_word(2)
is_word(None)

# %%
# If x is a number add three:
h = and_(is_number, plus_three)
# If x is a string, is it a word?:
g = and_(is_string, is_word)
# One or the other:
func = or_(h, g)
items = ["hello", "not-a-word", 2, None]
map(g, items)

# %%
Procedure = Callable[[], Any]

def if_(f: Variadic, g: Unary, h: Unary) -> Variadic:
  def i(*args, **kwargs):
    if (result := f(*args, **kwargs)):
      return g()
    return h()
  return i

# %% [markdown]
# # Interpreters

# %% [markdown]
# ## Operator Predicates

# %%

def binary_op(op: str) -> Optional[Callable[[Any, Any], Any]]:
  'Returns a function for a binary operator by name.'
  return BINARY_OPS.get(op)

BINARY_OPS = {
  '==': lambda a, b: a == b,
  '!=': lambda a, b: a != b,
  '<':  lambda a, b: a < b,
  '>':  lambda a, b: a > b,
  '<=': lambda a, b: a <= b,
  '>=': lambda a, b: a >= b,
  'and': lambda a, b: a and b,
  'or': lambda a, b: a or b,
}

binary_op('==') (2, 2)
binary_op('!=') (2, 2)

# %%
# Create a table where `x OP y` is true:
[
  f'{x} {op} {y}'
  for op in ['<', '==', '>']
  for x in (2, 3, 5)
  for y in (2, 3, 5)
  if binary_op(op)(x, y)
]

# %%
def op_pred(op: str, b: Any) -> Predicate | None:
  'Returns a predicate function given an operator name and a constant.'
  if pred := binary_op(op):
    return lambda a: pred(a, b)
  if op == "not":
    return lambda a: not a
  if op == "~=":
    return re_pred(b)
  if op == "~!":
    return not_(re_pred(b))
  return None

# %%
h = op_pred(">", 3)
h(2)
h(5)

# %%
g = op_pred("~=", 'ab+c')
g('')
g('ab')
g('abbbcc')

# %% [markdown]
# ## Sequencing

# %%
def progn(*fs: Sequence[Callable]) -> Callable:
  'Returns a function that calls each function in turn and returns the last result.'
  def g(*args, **kwargs):
    result = None
    for f in fs:
      result = f(*args, **kwargs)
    return result
  return g

# %%
def prog1(*fs: Sequence[Callable]) -> Callable:
  'Returns a function that calls each function in turn and returns the last result.'
  def g(*args, **kwargs):
    result = fs[0](*args, **kwargs)
    for f in fs[1:]:
      result = f(*args, **kwargs)
    return result
  return g

# %%
def reverse_apply(x: Any) -> Callable:
  return lambda f, *args, **kwargs: f(x, *args, **kwargs)

reverse_apply(1) (plus_three)

# %%
def demux(*funcs) -> Unary:
  'Return a function `h(x)` that returns `[f(x), g(x), ...].'
  return lambda x: map(reverse_apply(x), funcs)

demux(identity, len, compose(tuple, reversed))("abcd")

# %% [markdown]
# ## Parser Combinators

# %%
# Parser input: a sequence of lexemes:
Input = Sequence[Any]

# A parsed value and remaining input:
Parsed = Tuple[Any, Input]

# A parser matches the input sequence and produces a result or nothing:
Parser = Callable[[Input], Parsed | None]

# %%

def show_match(p: Parser) -> Variadic:
  def g(input: Input):
    return (p(input) or False, '<=', input)
  return g

# %%
first = at(0)
def rest(x: Input) -> Input:
  return x[1:]

def equals(x) -> Parser:
  'Returns a parser that matches `x`.'
  def g(input: input):
    y = first(input)
    logging.debug("equals(%s, %s)", repr(x), repr(y))
    if x == y:
      return (y, rest(input))
  return g

h = equals('a')
h(['a'])
h(['b', 2])


# %%
def which(p: Predicate) -> Parser:
  'Returns a parser for the next lexeme when `p(lexeme)` is true.'
  def g(input: Input):
    if p(first(input)):
      return (first(input), rest(input))
  return g

g = which(is_string)
g(['a'])
g([2])
g(['a', 'b'])

def alternation(*ps) -> Parser:
  def g(input):
    for p in ps:
      if (result := p(input)):
        return result
  return g

g = alternation(which(is_string), which(is_number))
g(['a'])
g([2])
g([False])


# %% [markdown]
# ## Sequence Parsers

# %%
ParsedSequence = Tuple[Sequence, Input]
SequenceParser = Callable[[Input], ParsedSequence | None]

def one(p: Parser) -> SequenceParser:
  'Returns a parser for one lexeme.'
  def g(input: Input):
    if input and (result := p(input)):
      parsed, input = result
      return ([parsed], input)
  return g

g = one(which(is_string))
g([])
g(['a'])
g([2])
g(['a', 'b'])


# %%
def zero_or_more(p: Parser) -> SequenceParser:
  'Returns a parser for zero or more lexemes.'
  def g(input: Input):
    acc = []
    while input and (result := p(input)):
      parsed, input = result
      acc.append(parsed)
    return (acc, input)
  return g

g = zero_or_more(which(is_string))
g([])
g(['a'])
g([2])
g(['a', 'b'])
g(['a', 'b', 2])
g(['a', 'b', 3, 5])

# %%
def one_or_more(p: Parser) -> SequenceParser:
  'Returns a parser for one or more lexemes as a sequence.'
  p = zero_or_more(p)
  def g(input: Input):
    if (result := p(input)) and len(result[0]) >= 1:
      return result
  return g

# %%
g = one_or_more(which(is_string))
g([])
g(['a'])
g([2])
g(['a', 'b'])
g(['a', 'b', 2])
g(['a', 'b', 3, 5])

# %%
def sequence_of(*parsers) -> SequenceParser:
  'Returns a parser for parsers of a sequence.'
  def g(input: Input):
    acc = []
    for p in parsers:
      if result := p(input):
        parsed, input = result
        acc.extend(parsed)
      else:
        return None
    return (acc, input)
  return g

g = sequence_of(one(which(is_string)), one(which(is_string)))
g([])
g(['a'])
g([2])
g(['a', 'b'])
g(['a', 'b', 2])
g(['a', 'b', 3, 5])

# %%
g = sequence_of(one_or_more(which(is_number)))
g([])
g(['a'])
g([2])
g([2, 3])
g([2, 3, False])

# %%
g = sequence_of(one(which(is_string)), one_or_more(which(is_number)))
g([])
g(['a'])
g([2])
g(['a', 'b'])
g(['a', 2])
g(['a', 2, 3])
g(['a', 2, 'b', 3])
g(['a', 2, 3, False])
g(['a', 2, 3, False, 'more'])

# %% [markdown]
# ## Parser Grammar

# %%

def take_while(f: Unary) -> Unary:
  def g(seq):
    acc = []
    while seq and (x := f(seq[0])):
      acc.append(x)
    return acc
  return g

# %% [markdown]
# ## Lexical Scanning

# %%
def eat(rx: str):
  p = re.compile(rx)
  return lambda s: re.sub(p, '', s)

def lexeme(pat: str, post = at(0)):
  post = post or (lambda m: m[0])
  rx = re.compile(pat)
  ws = eat(r'^\s+')
  def g(input):
    input = ws(input)
    if m := re.match(rx, input):
      return (post(m), input[len(m[0]):])
  return g

# %%

def cache(p):
  d = {}
  def g(input):
    if v := d.get(input):
      logging.debug('cached : %s => %s', repr(input), repr(v[0]))
      return v[0]
    v = p(input)
    d[input] = (v,)
    return v
  return g

# %%
def grammar_parser():
  env = {}
  def _(id):
    # nonlocal env
    # logging.debug('_(%s)', repr(id))
    return lambda *args: env[id](*args)

  def action(p: Parser, action: Unary) -> Parser:
    def g(input: Input):
      if result := p(input):
        value = action(result[0])
        return (value, result[1])
    return g

  def definition(id, p, act=None):
    log = partial(logging.debug, '  # %s')
    # p = trace(id, log, p)
    # p = cache(p)
    a = None
    if act is True:
      a = lambda x: (id, x)
    elif isinstance(act, str):
      a = lambda x: (act, x)
    elif act:
      a = act
    if a:
      p = action(p, a)
    env[id] = p

  definition('int',     lexeme(r'[-+]?\d+',               lambda m: ('int', int(m[0]))))
  definition('str'   ,  lexeme(r'"(\\"|\\?[^"]+)*"',      lambda m: ('str', eval(m[0]))))
  definition('re',      lexeme(r'/((\\/|(\\?[^/]+))*)/',  lambda m: ('re', re.compile(m[1]))))
  definition('name',    lexeme(r'[a-zA-Z][a-zA-Z0-9_]*',  lambda m: ('name', m[0])))
  definition('terminal', alternation(_("str"), _("re"), _('int')))
  definition('non-terminal', _('name'))
  definition('matcher', alternation(_('non-terminal'), _('terminal')))
  definition('binding', sequence_of(one(_('name')), one(lexeme(':')), one(_('matcher'))))
  definition('pattern', alternation(_('binding'), _('matcher')))
  definition('sequence_of',
    sequence_of(one_or_more(_('pattern'))))
  definition('alternation',
    sequence_of(one(_('sequence_of')), one(lexeme(r'\|')), one(_('production'))),
    lambda x: ('alternation', x[0], x[2]))
  definition('production',
    alternation(_('alternation'), _('sequence_of')))
  definition('definition',
    sequence_of(one(_('name')), one(lexeme(r"=")), one(_('production')), one(lexeme(r';'))),
    lambda x: ('definition', x[0], x[2]))
  definition('grammar',
    sequence_of(one_or_more(_('definition'))),
                'grammar')

  def g(input, start=None):
    start = start or 'grammar'
    return _(start)(input)
  return g

gram = grammar_parser()

# %%
def test(input, start=None):
  logging.debug("============================================\n")
  ic(input)
  result = gram(input, start)
  ic(start)
  ic(input)
  ic(result)

test('"asdf"', 'pattern')
test('  a = b c;')
test('a =b c|d;')
test('a = b c | d | e f;')
test('a = "foo";')
test('b = /foo/:c;')

# %%
#################################################
## Other
#################################################

def projection(key: Any, default: Any = None) -> Callable:
  'Returns a function `f(a)` that returns `a.get(key, default)`.'
  return lambda a: a.get(key, default)


# %% [markdown]
# # Other

# %% [markdown]
# ## Mapcat (aka Flat-Map)

# %%
ConcatableUnary = Callable[[Any], Sequence]

def mapcat(f: ConcatableUnary, xs: Sequence):
  'Concatenate the results of `map(f, xs)`.'
  return reduce(multiply, [], map(f, xs))

def duplicate(n, x):
  return [x] * n

duplicate_each_3_times = partial(mapcat, partial(duplicate, 3))
duplicate_each_3_times([".", "*"])
duplicate_each_3_times(range(4, 7))


# %% [markdown]
# ## Manipulating Arguments

# %%
def reverse_args(f: Callable) -> Callable:
  def g(*args, **kwargs):
    return f(*reversed(args), **kwargs)
  return g

def divide(x, y):
  return x / y

divide(2, 3)
reverse_args(divide)(2, 3)

reduce(reverse_args(multiply), " reversed ", a_list_of_strings)
reduce(reverse_args(conjoin), 2, [3, 5, 7])


