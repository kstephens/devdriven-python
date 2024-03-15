import re
from devdriven.util import get_safe, chunks, split_flat, parse_range, make_range
from devdriven.random import get_seed
from .command import Command, section, command
from .coerce import Coerce
from .util import select_columns, parse_col_or_index

section('Manipulation', 30)

@command
class Range(Command):
  '''
  range - Subset of rows.

  Aliases: r

  Arguments:

  start [end] [step]  |  For 1 or more arguments.
  [start]:[end]:step  |  Python-style range.

  Options:

  --start=START       |  Inclusive.  Default: 1.
  --end=END           |  Non-inclusive.  Default: last row.
  --step=STEP         |  Default: 1.

  # range: select a range of rows:
  $ psv in a.tsv // seq --start=0 // range 1 3 // md

  # range: every even row:
  $ psv in a.tsv // seq --start=0 // range --step=2 // md

  '''

  def xform(self, inp, _env):
    arg0 = get_safe(self.args, 0)
    rng = arg0 and parse_range(arg0, len(inp))
    if not rng:
      start = int(self.arg_or_opt(0, 'start', 0))
      end = int(self.arg_or_opt(1, 'end', len(inp)))
      step = int(self.arg_or_opt(2, 'step', 1))
      rng = make_range(start, end, step, len(inp))
    out = inp.iloc[rng]
    return out

def process_range(inp, start, end, step):
  return inp.iloc[make_range(start, end, step, len(inp))]

@command
class Head(Command):
  '''
  head - First N rows

  Aliases: h

  N : Default: 10

# head:
$ psv in us-states.txt // -table // head 5 // md

  '''
  def xform(self, inp, _env):
    count = int(self.arg_or_opt(0, 'count', 10))
    return process_range(inp, None, count, None)

@command
class Tail(Command):
  '''
  tail - Last N rows

  Aliases: t

  N : Default: 10

# tail: last 3 rows:
$ psv in us-states.txt // -table // tail 3 // md

  '''
  def xform(self, inp, _env):
    count = int(self.arg_or_opt(0, 'count', 10))
    return process_range(inp, - count, None, None)

@command
class Reverse(Command):
  '''
  reverse - Reverse rows.  Same as "range --step=-1"

  Aliases: tac

# reverse:
$ psv in a.tsv // seq // tac // md

  '''
  def xform(self, inp, _env):
    return process_range(inp, None, None, -1)

@command
class Shuffle(Command):
  '''
  shuffle - shuffle rows.

  Aliases: rand

  Options:

  --seed=SEED         |  String.  Default: use default state.'

$ psv in a.tsv // shuffle --seed=5 // md

  '''
  def xform(self, inp, _env):
    if seed := self.opt('seed', get_seed()):
      seed = int(seed + '0'.encode('utf-8').hex(), 16)
      # numpy.random._mt19937.MT19937._legacy_seeding
      # ValueError: Seed must be between 0 and 2**32 - 1
      seed = seed % ((2 ** 32) - 1)
    return inp.sample(frac=1, random_state=seed)

@command
class Cut(Command):
  '''
  cut - Cut specified columns.

  Aliases: c, x

  Arguments:

  NAME    |  Select name.
  I       |  Select index.
  COL:-   |  Remove column.
  *       |  Add all columns.
  NAME*   |  Any columns starting with "NAME".

# cut: select columns by index and name:
psv in a.tsv // cut 2,d // md

# cut: remove c, put d before other columns,
$ psv in a.tsv // cut d '*' c:- // md

  '''
  def xform(self, inp, _env):
    return inp[select_columns(inp, split_flat(self.args, ','))]

@command
class Uniq(Command):
  '''
  uniq - Return unique rows.

  Aliases: u
  '''
  def xform(self, inp, _env):
    return inp.drop_duplicates()

@command
class Sort(Command):
  '''
  sort - Sort rows by columns.
  Aliases: s

  Arguments:

  COL    |  Sort by COL ascending
  COL:-  |  Sort by COL descending
  COL:+  |  Sort by COL ascending

  Options:

  --reverse, -r     |  Sort descending.
  --numeric, -n     |  Sort as numeric.
  --coerce=TYPE     |  Sort by coerced value.

# sort: increasing:
$ psv in a.tsv // seq i // sort c // md

# sort: decreasing:
$ psv in a.tsv // seq i // sort -r c // md

# sort: by a decreasing, c increasing:
$ psv in a.tsv // seq i // md
$ psv in a.tsv // seq i // sort a:- c // md

  '''
  def xform(self, inp, _env):
    imp_cols = list(inp.columns)
    specified_cols = split_flat(self.args, ',') if self.args else imp_cols
    cols = []
    ascending = []
    default_order = '-' if self.opt('reverse') else '+'
    for col in specified_cols:
      order = default_order
      if mtch := re.match(r'^([^:]+):([-+]?)$', col):
        col = mtch.group(1)
        order = mtch.group(2)
      col = parse_col_or_index(imp_cols, col)
      cols.append(col)
      ascending.append(order != '-')
    key = None
    if self.opt('numeric'):
      key = 'numeric'
    elif self.opt('datetime'):
      key = 'datetime'
    else:
      key = self.opt('coerce')
    if key:
      key = Coerce().coercer(key)
    return inp.sort_values(by=cols, ascending=ascending, key=key)

@command
class Grep(Command):
  '''
  grep - Search for rows where columns match a regex.

  Aliases: g

  COL REGEX ...          |  Select rows where COL REGEX pairs match.
  REGEX                  |  Select rows where REGEX is applied to all columns.
  --all                  |  All patterns must match.
  --any                  |  Any pattern must match.
  --fixed-strings, -F    |  Match fixed string.
  --ignore-case, -i      |  Ignore case distinctions.
  --invert-match, -v     |  Invert the sense of matching, to select non-matching rows.

# grep: match columns by regex:
$ psv in a.tsv // grep d 'x' // md
$ psv in a.tsv // grep d '^x' // md
$ psv in a.tsv // grep d 'x.+p' // md

# grep: match where d contains "x" and b ends with "3":
$ psv in a.tsv // grep d 'x' b '3$' // md

  '''
  def __init__(self, *args):
    Command.__init__(self, *args)
    self.has_filter = None
    self.filter_expr = 0

  def xform(self, inp, _env):
    imp_cols = list(inp.columns)
    self.has_filter = None
    self.filter_expr = 0  # mock for: E1130: bad operand type for unary ~
    if len(self.args) == 1:
      for col in imp_cols:
        self.add_match(inp, col, self.args[0], 'any')
    else:
      for col, pat in chunks(self.args, 2):
        self.add_match(inp, col, pat, 'all')
    if self.has_filter:
      if self.opt('invert-match', False):
        # pylint: disable-next=invalid-unary-operand-type
        self.filter_expr = ~ self.filter_expr
      return inp[self.filter_expr]
    return inp

  def add_match(self, inp, col, pat, combine_default):
    if self.opt('fixed-strings'):
      pat = re.escape(pat)
    pat = f'.*{pat}'
    if self.opt('case-insensitive'):
      pat = f'(?i){pat}'
    rx = re.compile(pat)

    combine_opt = False
    if self.opt('all'):
      combine_opt = 'all'
    elif self.opt('any'):
      combine_opt = 'any'
    combine = combine_opt or combine_default

    match = None
    try:
      # https://stackoverflow.com/a/31076657/1141958
      # https://stackoverflow.com/a/52065957
      str_seq = inp[col].astype(str, errors='ignore').str
      # ic(str_seq)
      match = str_seq.match(rx, na=False)
    except (AttributeError, TypeError) as exc:
      self.log('warning', f'cannot match {pat!r} against column {col!r} : {exc}')
      return
    if self.has_filter:
      if combine == 'all':
        self.filter_expr = self.filter_expr & match
      elif combine == 'any':
        self.filter_expr = self.filter_expr | match
      else:
        raise Exception("grep : invalid combinator {combine!r}")
    else:
      self.has_filter = True
      self.filter_expr = match

@command
class Translate(Command):
  r'''
  translate - Translate characters.
  aliases: tr

  Similar to Unix tr command.

  SRC DST COL,...  |  Map chars from SRC to DST in each COL.
  -d DEL COL,...   |  Delete chars in DEL in each COL.
  --delete, -d     |  Delete characters.

# translate: change characters in specific field:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // tr ',' '_' Population // head // md

# translate: delete characters:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // tr -d ', ' // head // md

  '''
  def xform(self, inp, _env):
    if self.opt('delete'):
      trans = str.maketrans('', '', self.args[0])
      args = self.args[1:]
    else:
      trans = str.maketrans(*self.args[0:2])
      args = self.args[2:]
    cols = select_columns(inp, split_flat(args, ','), check=True, default_all=True)

    def xlate(x):
      return str(x).translate(trans)
    out = inp.copy()
    for col in cols:
      out[col] = out[col].apply(xlate)
    return out

@command
class NullXform(Command):
  '''
  null - Does nothing.

# null: does nothing:
$ psv in a.tsv // null IGNORED --OPTION=VALUE // md
'''
  def xform(self, inp, _env):
    return inp
