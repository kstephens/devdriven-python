from .base import Base, register
import json
import re
import subprocess
import sys
from io import StringIO
from collections import OrderedDict, Counter
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

class Cut(Base):
  def xform(self, inp):
    selected = []
    for col in self.args:
      action = '+'
      if mtch := re.match(r'^([^:]+):([-+]?)$', col):
        col = mtch.group(1)
        action = mtch.group(2)
      if col == '*':
        cols = list(inp.columns)
      else:
        cols = [col]
      if action == '-':
        selected = [x for x in selected if x not in cols]
      else:
        selected = selected + [x for x in cols if x not in selected]
    return inp[selected]
register(Cut, 'cut', ['x'],
         synopsis="Cut specified columns.",
         args={
           'COL ...': 'List of columms to select',
           '*': 'Add all columns.',
           'COL:-': "Remove column.",
         })

class Sort(Base):
  def xform(self, inp):
    specified_cols = self.args if self.args else list(inp.columns)
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
register(Sort, 'sort', [],
         synposis="Sort rows by columns.",
         args={'COL': "Sort by COL ascending",
               "COL:-": "Sort by COL descending",
               "COL:+": "Sort by COL ascending",
         })

class Grep(Base):
  # Alternate: scan multiple times.
  def xform_(self, inp):
    out = inp
    # https://stackoverflow.com/a/31076657/1141958
    for col, pat in chunks(self.args, 2):
      out = out[out[col].str.match(re.compile(pat))]
    return out

  def xform(self, inp):
    filter = has_filter = None
    # https://stackoverflow.com/a/31076657/1141958
    for col, pat in chunks(self.args, 2):
      # ic(col); ic(pat)
      match = inp[col].str.match(re.compile(pat))
      if has_filter:
        filter = filter & match
      else:
        filter = match
      has_filter = True
    if has_filter:
      return inp[filter]
    return inp
register(Grep, 'grep', ['g'],
         synopsis='Search for rows where each column matches a regex.',
         args={'COL REGEX ...': 'List of NAME REGEX pairs.'})

def chunks(xs, n):
  n = max(1, n)
  return (xs[i:i+n] for i in range(0, len(xs), n))

class AddSequence(Base):
  def xform(self, inp):
    start = int(self.opt('start', 1))
    step  = int(self.opt('step', 1))
    col   = (self.args and self.args[0]) or '__i__'
    out = inp.copy()
    out[col] = range(start, start + len(out) * step, step)
    return out
register(AddSequence, 'add-sequence', [''],
         synposis="Add a column with a sequence of numbers.",
         args={'NEW-COLUMN': "defaults to __i__"},
         opts={'start': 'start at: defaults to 1.',
               'step':  'step by: defaults to 1.'})

#############
# metadata

class Columns(Base):
  def xform(self, inp):
    out = get_dataframe_info(inp)
    out.reset_index(inplace=True)
    out['index'] = out.index
    out = out.rename(columns={'features':'name'})
    return out
register(Columns, 'columns', ['cols'],
         synopsis="returns a table of column names and attributes.")

def get_dataframe_info(df):
  df_types = pd.DataFrame(df.dtypes)
  df_nulls = df.count()
  df_null_count = pd.concat([df_types, df_nulls], axis=1)
  df_null_count = df_null_count.reset_index()
  # Reassign column names
  col_names = ["features", "types", "non_null_counts"]
  df_null_count.columns = col_names
  # Add this to sort
  # df_null_count = df_null_count.sort_values(by=["null_counts"], ascending=False)
  return df_null_count

class Stats(Base):
  def xform(self, inp):
    out = inp.describe()
    out['stat'] = out.index
    return out
register(Stats, 'stats', ['describe'],
         synopsis="basic stats of numeric columns")

