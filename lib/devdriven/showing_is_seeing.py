# import readline
import re
import sys
import os
import logging
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

ic.configureOutput(includeContext=True)

class ShowingIsSeeing:
  def __init__(self, bindings=None):
    self.enabled = True
    self.repl_enabled = int(os.environ.get('SIS_REPL_ENABLED', '1')) != 0
    self.print_enabled = True
    self.bindings = bindings
    self.lexer = PythonLexer()
    self.formatter = Terminal256Formatter(style=SolarizedDark)
    self.debug = False
    self.term_cols = 80
    self.horiz_bar = f'{rgb_24bit(50, 50, 50)}{"_" * self.term_cols}{ANSI_NORMAL}'
    self.comment_block = '#' * self.term_cols
    readline.clear_history()

  def setup_logging(self):
    logging.basicConfig(
      stream=sys.stderr,
      level=logging.DEBUG,
      format='',
    )
    return self

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
    last_value = last_expr = None
    while expr := self.read_line(prompt):
      try:
        last_value, context = self.eval_expr(expr)
        self.print_eval_result(last_value, context)
        last_expr = expr
      # pylint: disable-next=broad-except
      except Exception as exc:
        self.print(f'{ERROR_COLOR}{exc!r}{ANSI_NORMAL}')
        self.print(f'in: {ERROR_COLOR}{expr!r}{ANSI_NORMAL}')
    return last_value, last_expr

  def expr_is_stmt(self, expr):
    if re.search(r'^\s*(from|import)\s+', expr):
      return True
    if self.is_assignment(expr):
      return True
    if re.search(r'^[\[\{\(]', expr):
      return False
    return self.is_multiline(expr)

  def is_assignment(self, expr):
    return re.search(r'^[a-zA-Z_][a-zA-Z0-9_.]*\s+=\s+', expr)

  def is_multiline(self, expr):
    return '\n' in expr

  def eval_expr(self, expr, is_stmt=False, history=True):
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
    if history and not self.is_multiline(expr):
      readline.add_history(expr)

    # pprint(locals)
    # Copy new locals back into bindings:
    for key, val in local_bindings.items():
      if key not in context:  # .keys():
        # pprint((key, val))
        bindings[key] = val
    return (local_bindings['_value'], context)

  def print_eval_result(self, value, context):
    if not context['_is_stmt']:
      self.write(RESULT_SEP)
      self.print_value(value)
      self.write('\n')
    return value

  def eval_and_print_and_repl(self, expr, repl=True, print=True):
    repl = repl and self.repl_enabled
    print = print and self.print_enabled
    if False:  # self.debug:
      ic(expr)
      ic(repl)
      ic(print)
    if self.expr_is_stmt(expr):
      if print:
        self.print_expr(expr)
      value, context = self.eval_expr(expr)
      if repl:
        self.print('')
        self.repl(REPL_PROMPT)
    else:
      if print:
        self.print_expr(expr)
      if repl:
        _repl_value, repl_expr = self.repl(QUESTION_PROMPT)
        if print and repl_expr:
          self.print_expr(expr)
          self.write(RESULT_SEP)
      value, context = self.eval_expr(expr)
      if print:
        self.print_eval_result(value, context)
        self.write('\n')
    if print:
      self.write(self.horiz_bar + '\n')
    return value

  def if_print_enabled(self, f):
    def g(*args, **kwargs):
      if self.print_enabled:
        return f(*args, **kwargs)
    return g

  # pylint: disable-next=too-many-arguments
  def scan_lines(self, lines, eval_and_print_expr, eval_expr, print_expr, comment):
    buffer = ''
    line = m = None

    def emit():
      nonlocal buffer
      if buffer:
        # ic(buffer)
        eval_and_print_expr(buffer)
        buffer = ''

    def log(msg, *args):
      nonlocal line
      if self.debug:
        msg = f"scan_lines: %s : {msg}"
        logging.debug(msg, pformat(line), *args, )

    prev_line = None
    for line in lines.splitlines():
      log('line')
      log('buffer = %s', pformat(buffer))
      if m := re.search(r'^### *SIS: *(.*)', line):
        stmt = m[1]
        log('SIS: stmt = %s', pformat(stmt))
        eval_expr(stmt, is_stmt=True, history=False)
        continue
      if not self.enabled:
        continue
      if line.startswith('#'):
        log('block-comment')
        emit()
        if line.startswith('####'):
          comment(self.comment_block)
        else:
          comment(line)
      elif m := re.search(r'^\s*(from|import)\s+', line):
        log('import')
        emit()
        eval_expr(line, is_stmt=True, history=False)
      elif m := self.is_assignment(line):
        log('top-level-assignment')
        emit()
        print_expr(line)
        eval_expr(line, is_stmt=True)
      elif m := re.search(r'^(((class|def|if|elif|else|try|except|finally|return)\b)|""""|\'\'\')', line):
        log('statement')
        buffer += line + '\n'
      elif m := re.search(r'(""""|\'\'\')\s*', line):
        log('multiline-string')
        buffer += line + '\n'
      elif m := re.search(r'[\[\{\(:]\s*(#.*)?$', line):
        log('open-delmiter')
        buffer += line + '\n'
      elif m := re.search(r'^[\]\}\)]', line):
        log('close-delmiter')
        buffer += line + '\n'
        emit()
      elif m := re.search(r'^\s+\S', line):
        log('indented')
        buffer += line + '\n'
      elif m := re.search(r'^\s*$', line):
        log('blank-line')
        emit()
        comment(line)
        if prev_line.startswith('###') and self.repl_enabled:
          self.repl(REPL_PROMPT)
          self.print('')
      else:
        log('other')
        emit()
        buffer = line
        emit()
      prev_line = line
      if self.debug and m:
        ic(m.groups())
    emit()

  def eval_exprs(self, lines):
    self.scan_lines(
      lines,
      self.eval_and_print_and_repl,
      self.eval_expr,
      self.if_print_enabled(self.print_expr),
      self.if_print_enabled(self.print_comment),
    )


def clean_str(x):
  return re.sub(r'[\001\002]', '', str(x))

# https://stackoverflow.com/a/55773513/1141958
def rl_ansi(text):
  return f'\001{text}\002'

# pylint: disable-next=invalid-name
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
