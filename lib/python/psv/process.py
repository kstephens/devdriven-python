import re
import pandas as pd
from devdriven.util import chunks, split_flat, parse_range, make_range
from devdriven.pandas import count_by
from .command import Command, command
from .metadata import Coerce
from .util import *

@command()
class Range(Command):
  '''
  range - Subset of rows.

  Aliases: r

  Arguments:

  start [end] [step] | For 1 or more arguments.
  [start]:[end]:step | Python-style range.

  Options:

  --start=START | Inclusive.  Default: 1.
  --end=END     | Non-inclusive.  Default: last row.
  --step=STEP   | Default: 1.

  # range: select a range of rows:
  $ psv in -i a.tsv // seq --start=0 // range 1 3 // md

  # range: every even row:
  $ psv in -i a.tsv // seq --start=0 // range --step=2 // md

  '''

  def xform(self, inp, _env):
    arg0 = get_safe(self.args, 0)
    rng = arg0 and parse_range(arg0, len(inp))
    if not rng:
      start = int(self.arg_or_opt(0, 'start', 0))
      end  =  int(self.arg_or_opt(1, 'end', len(inp)))
      step  = int(self.arg_or_opt(2, 'step', 1))
      rng = make_range(start, end, step, len(inp))
    out = inp.iloc[rng]
    return out

def process_range(inp, start, end, step):
  return inp.iloc[make_range(start, end, step, len(inp))]

@command()
class Head(Command):
  '''
  head - First N rows

  Aliases: h

  N : Default: 10

# head:
$ psv in us-states.txt // -table // head 5 // md

  '''
  def xform(self, inp, _env):
    count = abs(int(self.arg_or_opt(0, 'count', 10)))
    return process_range(inp, None, count, None)

@command()
class Tail(Command):
  '''
  tail - Last N rows

  Aliases: t

  N : Default: 10

# tail: last 3 rows:
$ psv in us-states.txt // -table // tail 3 // md

  '''
  def xform(self, inp, _env):
    count = abs(int(self.arg_or_opt(0, 'count', 10)))
    return process_range(inp, - count, None, None)

@command()
class Reverse(Command):
  '''
  reverse - Reverse rows.  Same as "range --step=-1"

  Aliases: tac

# reverse:
$ psv in -i a.tsv // seq // tac // md

  '''
  def xform(self, inp, _env):
    return process_range(inp, None, None, -1)

@command()
class Cut(Command):
  '''
  cut - Cut specified columns.

  Aliases: c, x

  Arguments:

  NAME     | Select name.
  I       | Select index.
  COL:-   | Remove column.
  *       | Add all columns.
  NAME*   | Any columns starting with "NAME".

# cut: select columns by index and name:
psv in -i a.tsv // cut 2,d // md

# cut: remove c, put d before other columns,
$ psv in -i a.tsv // cut d '*' c:- // md

  '''
  def xform(self, inp, _env):
    return inp[select_columns(inp, split_flat(self.args, ','))]

@command()
class Uniq(Command):
  '''
  uniq - Return unique rows.

  Aliases: u
  '''
  def xform(self, inp, _env):
    return inp.drop_duplicates()

@command()
class Sort(Command):
  '''
  sort - Sort rows by columns.
  Aliases: s

  Arguments:

  COL   | Sort by COL ascending
  COL:- | Sort by COL descending
  COL:+ | Sort by COL ascending

  Options:

  -r | Sort descending.
  -n | Coerce columns to numeric.

# sort: decreasing:
$ psv in -i a.tsv // sort -r a // md

# sort: by a decreasing, c increasing,
# remove c, put d before other columns,
# create a column i with a seqence
$ psv in -i a.tsv // sort a:- c // cut d '*' c:- // seq i 10 5 // md

  '''
  def xform(self, inp, _env):
    imp_cols = list(inp.columns)
    specified_cols = split_flat(self.args, ',') if self.args else imp_cols
    cols = []
    ascending = []
    default_order = '-' if self.opt('r') else '+'
    for col in specified_cols:
      order = default_order
      if mtch := re.match(r'^([^:]+):([-+]?)$', col):
        col = mtch.group(1)
        order = mtch.group(2)
      col = parse_col_or_index(imp_cols, col)
      cols.append(col)
      ascending.append(order != '-')
    key = Coerce().coercer('numeric') if self.opt('n') else None
    return inp.sort_values(by=cols, ascending=ascending, key=key)

@command()
class Grep(Command):
  '''
  grep - Search for rows where each column matches a regex.

  Aliases: g

  Arguments:

  COL REGEX ... | List of NAME REGEX pairs.

# grep: match columns by regex:
$ psv in -i a.tsv // grep d '.*x.*' // md

# grep: match d and b:
$ psv in -i a.tsv // grep d '.*x.*' b '.*3$' // md

  '''
  def xform(self, inp, _env):
    imp_cols = list(inp.columns)
    filter_expr = has_filter = None
    for col, pat in chunks(self.args, 2):
      col = parse_col_or_index(imp_cols, col)
      # https://stackoverflow.com/a/31076657/1141958
      match = inp[col].str.match(re.compile(pat), na=False)
      filter_expr = filter_expr & match if has_filter else match
      has_filter = True
    if has_filter:
      return inp[filter_expr]
    return inp

@command()
class Count(Command):
  '''
  count - Count of unique column values.

  Arguments:

  COL ... | Columns to group by.  Default: ALL C.

  Options:

  --column= | Default: "__count__"
  '''
  def xform(self, inp, _env):
    count_col = self.opt('column', '__count__')
    group_cols = select_columns(inp, split_flat(self.args, ','), check=True)
    if not group_cols:
      group_cols = list(inp.columns)
    return count_by(inp, group_cols, sort_by=group_cols, name=count_col)

@command()
class Translate(Command):
  '''
  translate - Translate characters.
  aliases: tr

  Similar to Unix tr command.

  SRC DST COL... : Map chars from SRC to DST in each COL.
  -d DEL COL...  : Delete chars in DEL in each COL.
  -d             : Delete characters.

# translate: change characters in specific field:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // tr ',' '_' Population // head // md

# translate: delete characters:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // tr -d ', ' // head // md

  '''
  def xform(self, inp, _env):
    if self.opt('d'):
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

@command()
class Stats(Command):
  '''
  stats - Basic stats of numeric columns.
  aliases: describe

# stats: basic stats:
$ psv in a.tsv // -tsv // stats // md

  '''
  def xform(self, inp, _env):
    out = inp.describe()
    out['stat'] = out.index
    return out

@command()
class NullXform(Command):
  '''
  null - Does nothing.

# null: does nothing:
$ psv in -i a.tsv // null IGNORED --OPTION=VALUE // md
'''
  def xform(self, inp, _env):
    return inp
