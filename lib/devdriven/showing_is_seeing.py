# import readline
import re
import sys
from pprint import pformat
from pygments import highlight
from pygments.lexers.python import PythonLexer
from pygments.formatters.terminal256 import Terminal256Formatter
from icecream.coloring import SolarizedDark

class ShowingIsSeeing:
  def __init__(self, bindings=None):
    self.bindings = bindings
    self.lexer = PythonLexer()
    self.formatter = Terminal256Formatter(style=SolarizedDark)

  def write(self, x):
    sys.stdout.write(str(x))

  def print(self, x):
    sys.stdout.write(str(x) + '\n')

  def highlight_expr(self, expr):
    return highlight(expr, self.lexer, self.formatter).strip()

  def format_value(self, value):
    rep = pformat(value,
                  indent=2,
                  width=80,
                  depth=None,
                  compact=True,
                  sort_dicts=True,
                  underscore_numbers=False)
    return self.highlight_expr(rep)

  def print_value(self, value):
    rep = self.format_value(value)
    rep = re.sub(r'^', '  ', rep, flags=re.MULTILINE)
    if callable(value):
      if doc := getattr(value, '__doc__', None):
        rep += f"\n  '''{doc}'''"
    self.write(rep)

  def exec_and_print_value(self, expr):
    bindings = (self.bindings or globals)()
    context = {'_expr': expr, '_value': None, '_self': self}
    local_bindings = context | {}
    # pylint: disable-next=exec-used
    exec(f'_value = ({expr});', bindings, local_bindings)
    # pprint(locals)
    # Copy new locals back into bindings:
    for key, val in local_bindings.items():
      if key not in context:  # .keys():
        # pprint((key, val))
        bindings[key] = val
    self.print_value(local_bindings['_value'])
    self.write('\n\n')

  def print_expr(self, expr, arrow=''):
    expr = self.highlight_expr(expr)
    self.write(f'{expr}{arrow}')

  def print_and_exec(self, expr):
    self.print_expr(expr)
    self.exec_and_print_value(expr)

  def prompt_and_print(self, expr):
    user_expr_given = None
    self.print_expr(expr, '')
    while user_expr := input(' => '):
      user_expr_given = user_expr
      self.print_and_exec(user_expr)
      self.write('\n')
    if user_expr_given:
      self.print_expr(expr, arrow=' => \n')
    self.exec_and_print_value(expr)

  def eval_exprs(self, exprs):
    for expr in exprs.splitlines():
      expr = expr.strip()
      if expr.startswith('#') or expr == '':
        self.print(expr)
      else:
        self.prompt_and_print(expr)
