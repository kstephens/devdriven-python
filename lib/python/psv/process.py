import re
import pandas as pd
from devdriven.util import chunks, split_flat, parse_range, make_range
from devdriven.pandas import count_by
from .command import Command, command
from .metadata import Coerce
from .util import *

@command('range', ['r'],
         synopsis="Select a sequence of rows.",
         args={'start [end] [step]': "For 1 or more arguments.",
               '[start]:[end]:step': "Python-style range."},
         opts={'start': 'start at: defaults to 1.',
               'step':  'step by: defaults to 1.'})
class Range(Command):
  def xform(self, inp, _env):
    arg0 = get_safe(self.args, 0)
    rng = arg0 and parse_range(arg0, len(inp))
    if not rng:
      start = int(self.arg_or_opt(0, 'start', 0))
      end  =  int(self.arg_or_opt(1, 'end', len(inp)))
      step  = int(self.arg_or_opt(2, 'step', 1))
      rng = make_range(start, end, step, len(inp))
    out = inp.iloc[rng]
    #if r.step < 0:
    #  out = out.iloc[::-1]
    return out

def process_range(inp, start, end, step):
  return inp.iloc[make_range(start, end, step, len(inp))]

@command('head', ['h'],
         synopsis='First N rows')
class Head(Command):
  def xform(self, inp, _env):
    count = abs(int(self.arg_or_opt(0, 'count', 10)))
    return process_range(inp, None, count, None)

@command('tail', ['t'],
         synopsis='Last N rows')
class Tail(Command):
  def xform(self, inp, _env):
    count = abs(int(self.arg_or_opt(0, 'count', 10)))
    return process_range(inp, - count, None, None)

@command('reverse', ['tac'],
         synopsis='Reverse rows.  Same as "range --step -1"')
class Reverse(Command):
  def xform(self, inp, env):
    return process_range(inp, None, None, -1)

@command('cut', ['c', 'x'],
         synopsis="Cut specified columns.",
         args={
           'COL ...': 'List of columms to select',
           '*': 'Add all columns.',
           'COL:-': "Remove column.",
         })
class Cut(Command):
  def xform(self, inp, _env):
    return inp[select_columns(inp, split_flat(self.args, ','))]

@command('uniq', ['u'],
         synopsis="Return unique rows.",
         args={
         })
class Uniq(Command):
  def xform(self, inp, _env):
    return inp.drop_duplicates()

@command('sort', ['s'],
         synposis="Sort rows by columns.",
         args={'COL': "Sort by COL ascending",
               "COL:-": "Sort by COL descending",
               "COL:+": "Sort by COL ascending",
         },
         opts={'r': 'Sort descending.',
               'n': 'Coerce columns to numeric.'})
class Sort(Command):
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

@command('grep', ['g'],
         synopsis='Search for rows where each column matches a regex.',
         args={'COL REGEX ...': 'List of NAME REGEX pairs.'})
class Grep(Command):
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

@command('count', [],
         synopsis="Count of unique column values.",
         args={'COL ...': "Columns to group by.  Defaults to all columns."},
         opts={'column': "Defaults to __count__"})
class Count(Command):
  def xform(self, inp, _env):
    count_col = self.opt('column', '__count__')
    group_cols = select_columns(inp, split_flat(self.args, ','), check=True)
    if not group_cols:
      group_cols = list(inp.columns)
    return count_by(inp, group_cols, sort_by=group_cols, name=count_col)

@command('translate', ['tr'],
         synopsis="Translate characters.",
         args={
           'SRC DST COL...': 'Map chars from SRC to DST in each COL.',
           '-d DEL COL...': 'Delete chars in DEL in each COL.',
         },
         opts={
           '-d': 'Delete characters.',
         })
class Translate(Command):
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

@command('stats', ['describe'],
         synopsis="Basic stats of numeric columns.")
class Stats(Command):
  def xform(self, inp, _env):
    out = inp.describe()
    out['stat'] = out.index
    return out

@command('null', [],
         synopsis="Does nothing.")
class NullXform(Command):
  def xform(self, inp, _env):
    return inp
