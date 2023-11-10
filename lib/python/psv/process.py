import re
import pandas as pd
from devdriven.util import chunks, flat_map, split_flat, parse_range, make_range
from devdriven.pandas import remove_index, count_by
from .command import Command, command
from .util import *

@command('range', [],
         synopsis="Select a sequence of rows.",
         args={'start [end] [step]': "For 1 or more arguments.",
               '[start]:[end]:step': "Python-style range."},
         opts={'start': 'start at: defaults to 1.',
               'step':  'step by: defaults to 1.'})
class Range(Command):
  def xform(self, inp, _env):
    arg0 = get_safe(self.args, 0)
    r = arg0 and parse_range(arg0, len(inp))
    if not r:
      start = int(self.arg_or_opt(0, 'start', 0))
      end  =  int(self.arg_or_opt(1, 'end', len(inp)))
      step  = int(self.arg_or_opt(2, 'step', 1))
      r = make_range(start, end, step, len(inp))
    out = inp.iloc[r]
    #if r.step < 0:
    #  out = out.iloc[::-1]
    return out

@command('reverse', ['tac'],
         synopsis='Reverse rows.  Same as "range --step -1"')
class Reverse(Command):
  def xform(self, inp, env):
    return self.make_xform(['range', '--step', '-1']).xform(inp, env)

@command('cut', ['x'],
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

@command('sort', [],
         synposis="Sort rows by columns.",
         args={'COL': "Sort by COL ascending",
               "COL:-": "Sort by COL descending",
               "COL:+": "Sort by COL ascending",
         })
class Sort(Command):
  def xform(self, inp, _env):
    imp_cols = list(inp.columns)
    specified_cols = split_flat(self.args, ',') if self.args else imp_cols
    cols = []
    ascending = []
    for col in specified_cols:
      order = '+'
      if mtch := re.match(r'^([^:]+):([-+]?)$', col):
        col = mtch.group(1)
        order = mtch.group(2)
      col = parse_col_or_index(imp_cols, col)
      cols.append(col)
      ascending.append(order != '-')
    return inp.sort_values(by=cols, ascending=ascending)

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
      match = inp[col].str.match(re.compile(pat))
      filter_expr = filter_expr & match if has_filter else match
      has_filter = True
    if has_filter:
      return inp[filter_expr]
    return inp

@command('count', [],
         synopsis="Count of records by group.",
         args={'COL ...': "Columns to group by.  If not specified, one row with the count column is returned."},
         opts={'column': "defaults to __count__"})
class Count(Command):
  def xform(self, inp, _env):
    count_col = self.opt('column', '__count__')
    group_cols = select_columns(inp, split_flat(self.args, ','), check=True)
    if not group_cols:
      return pd.DataFrame(columns=[count_col], data=[[len(inp)]])
    return count_by(inp, group_cols, sort_by=group_cols, name=count_col)

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
