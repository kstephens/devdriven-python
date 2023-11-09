import re
from devdriven.util import chunks, flat_map, split_flat
from devdriven.pandas import remove_index, count_by
from .command import Command, command
from .util import *

@command('range', [],
         synopsis="Select a sequence of rows.",
         args={'start': "defaults to __i__"},
         opts={'start': 'start at: defaults to 1.',
               'step':  'step by: defaults to 1.'})
class Range(Command):
  def xform(self, inp, _env):
    start = int(self.arg_or_opt(0, 'start', 0))
    end  =  int(self.arg_or_opt(1, 'end', len(inp)))
    step  = int(self.arg_or_opt(2, 'step', 1))
    reverse = False
    if end < start:
      start, end = end, start
    if step < 0:
      step = - step
      reverse = True
    index = range(start, end, step)
    out = inp.iloc[index]
    if reverse:
      out = out.iloc[::-1]
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
    return inp[select_columns(inp, split_flat(self.args))]

@command('sort', [],
         synposis="Sort rows by columns.",
         args={'COL': "Sort by COL ascending",
               "COL:-": "Sort by COL descending",
               "COL:+": "Sort by COL ascending",
         })
class Sort(Command):
  def xform(self, inp, _env):
    specified_cols = self.args if split_flat(self.args) else list(inp.columns)
    cols = []
    ascending = []
    for col in specified_cols:
      order = '+'
      if mtch := re.match(r'^([^:]+):([-+]?)$', col):
        col = mtch.group(1)
        order = mtch.group(2)
      cols.append(col)
      ascending.append(order != '-')
    return inp.sort_values(by=cols, ascending=ascending)

@command('grep', ['g'],
         synopsis='Search for rows where each column matches a regex.',
         args={'COL REGEX ...': 'List of NAME REGEX pairs.'})
class Grep(Command):
  def xform(self, inp, _env):
    filter_expr = has_filter = None
    # https://stackoverflow.com/a/31076657/1141958
    for col, pat in chunks(self.args, 2):
      match = inp[col].str.match(re.compile(pat))
      if has_filter:
        filter_expr = filter_expr & match
      else:
        filter_expr = match
      has_filter = True
    if has_filter:
      return inp[filter_expr]
    return inp

@command('count', [],
         synopsis="Count of records by group.",
         args={'column': "defaults to count"})
class Count(Command):
  def xform(self, inp, _env):
    count = self.opt('column', 'count')
    by = select_columns(inp, split_flat(self.args), check=True)
    return count_by(inp, by, sort_by=by, name=count)

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
