# import readline
import re
import sys
try:
  import gnureadline as readline
except ImportError:
  import readline
from pprint import pformat
from pygments import highlight
from pygments.lexers.python import PythonLexer
from pygments.formatters.terminal256 import Terminal256Formatter
from icecream.coloring import SolarizedDark
from icecream import ic


class ShowingIsSeeing:
  def __init__(self, bindings=None):
    self.repl_enabled = True
    self.bindings = bindings
    self.lexer = PythonLexer()
    self.formatter = Terminal256Formatter(style=SolarizedDark)
    readline.clear_history()

  def write(self, x):
    sys.stdout.write(clean_str(x))

  def print(self, x):
    self.write(str(x) + '\n')

  def highlight_expr(self, expr):
    return highlight(expr, self.lexer, self.formatter).strip()

  def highlight_comment(self, value):
    return f'{COLOR_COMMENT}{value}{ANSI_NORMAL}'
    # return highlight(value, self.lexer, self.formatter)

  def format_value(self, value):
    rep = pformat(value,
                  indent=2,
                  width=80,
                  depth=None,
                  compact=True,
                  sort_dicts=True,
                  underscore_numbers=False)
    return self.highlight_expr(rep)

  def print_value(self, value, indent='   '):
    rep = self.format_value(value)
    if callable(value):
      if doc := getattr(value, '__doc__', None):
        if '\n' in doc:
          rep += f"\n  '''{doc}'''"
        else:
          rep += f"\n  '{doc}'"
    rep = re.sub(r'^', indent, rep, flags=re.MULTILINE)
    rep = rep.removeprefix(indent)
    self.write(rep)

  def print_comment(self, value):
    self.write(self.highlight_comment(value) + '\n')

  def print_expr(self, expr):
    self.print(self.highlight_expr(expr))

  def read_line(self, prompt):
    return input(prompt)

  def repl(self, prompt):
    last_expr = last_value = None
    while expr := self.read_line(prompt):
      self.print_expr(expr)
      try:
        last_value = self.exec_and_print(expr)
        last_expr = expr
      except Exception as e:
        self.print(f'{ERROR_COLOR}{e!r}{ANSI_NORMAL}')
        self.print(f'in: {ERROR_COLOR}{expr!r}{ANSI_NORMAL}')
    return last_value, last_expr

  def expr_is_stmt(self, expr):
    if re.search(r'^\s*(from|import)\s+', expr):
      return True
    if re.search(r'^[a-zA-Z_][a-zA-Z0-9_]*\s+=\s+', expr):
      return True
    return self.is_multiline(expr)

  def is_multiline(self, expr):
    return '\n' in expr

  def eval_expr(self, expr, is_stmt=False, no_history=False):
    bindings = (self.bindings or globals)()
    context = {
      '_is_stmt': (is_stmt or self.expr_is_stmt(expr)),
      '_expr': expr,
      '_value': None,
      '_sis': self
    }
    local_bindings = context | {}
    if context['_is_stmt']:
      executable = expr
    else:
      expr = re.sub(r'\s*#.*', '', expr)
      executable = f'_value = ({expr});'
    # ic(executable)
    # pylint: disable-next=exec-used
    exec(executable, bindings, local_bindings)
    if not (no_history or self.is_multiline(expr)):
      readline.add_history(expr)

    # pprint(locals)
    # Copy new locals back into bindings:
    for key, val in local_bindings.items():
      if key not in context:  # .keys():
        # pprint((key, val))
        bindings[key] = val
    return (context, local_bindings['_value'])

  def exec_and_print(self, expr):
    context, value = self.eval_expr(expr)
    if not context['_is_stmt']:
      self.write(RESULT_SEP)
      self.print_value(value)
    self.write('\n')
    return value

  def prompt_eval_print(self, expr):
    expr_given = None
    if self.expr_is_stmt(expr):
      self.print_expr(expr)
      self.eval_expr(expr)
      if self.repl_enabled:
        self.repl(REPL_PROMPT)
    else:
      self.print_expr(expr)
      if self.repl_enabled:
        expr_given, _value = self.repl(QUESTION_PROMPT)
        if expr_given:
          self.print_expr(expr)
          self.write(RESULT_SEP)
      self.exec_and_print(expr)
    self.write(HORIZ_BAR + '\n')

  def scan_lines(self, lines, eval_and_print_expr, eval_expr, print_expr, comment):
    ready = True
    buffer = ''
    def emit():
      nonlocal buffer
      if buffer:
        # ic(buffer)
        eval_and_print_expr(buffer)
        buffer = ''
    prev_line = None
    for line in lines.splitlines():
      # ic(line)
      if re.search(r'^### SIS: BEGIN', line):
        ready = True
        continue
      if re.search(r'^### SIS: END', line):
        ready = False
        continue
      if not ready:
        continue
      if line.startswith('#'):
        emit()
        comment(line)
      elif re.search(r'^\s*(from|import)\s+', line):
        eval_expr(line, is_stmt=True, no_history=True)
      elif re.search(r'^[a-zA-Z_][a-zA-Z0-9_.]*\s+=\s+', line):
        print_expr(line)
        eval_expr(line, is_stmt=True)
      elif re.search(r'^(def|if|elif|else|try|except|finally|return|""""|\'\'\')', line):
        buffer += line + '\n'
      elif re.search(r'^\s+\S', line):
        buffer += line + '\n'
      elif re.search(r'^\s*$', line):
        emit()
        comment(line)
        if prev_line.startswith('###') and self.repl_enabled:
          self.repl(REPL_PROMPT)
      else:
        emit()
        buffer = line
        emit()
      prev_line = line
    emit()

  def eval_exprs(self, lines):
    self.scan_lines(
      lines,
      self.prompt_eval_print,
      self.eval_expr,
      self.print_expr,
      self.print_comment,
    )


def clean_str(x):
  return re.sub(r'[\001\002]', '', str(x))

# https://stackoverflow.com/a/55773513/1141958
def rl_ansi(text):
  return f'\001{text}\002'

def rgb_24bit(r, g, b):
  return rl_ansi(f'\033[38;2;{r};{g};{b}m')

ANSI_NORMAL = rl_ansi('\033[0m')
ANSI_BLINK = rl_ansi('\033[5m')
ANSI_BLINK_FAST = rl_ansi('\033[6m')
COLOR_COMMENT = rgb_24bit(150, 150, 0)
RESULT_SEP = f'{rgb_24bit(90, 140, 176)}=>{ANSI_NORMAL} '
REPL_PROMPT = f'{rgb_24bit(90, 140, 176)}#>{ANSI_NORMAL} '
QUESTION_PROMPT = f'{rgb_24bit(217, 101, 72)}#{ANSI_BLINK}?{ANSI_NORMAL} '
ERROR_COLOR = rgb_24bit(255, 50, 50)
HORIZ_BAR = f'{rgb_24bit(50, 50, 50)}{"_" * 80}{ANSI_NORMAL}'
