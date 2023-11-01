from .base import Base, register
import json
import re
import subprocess
import sys
from devdriven.util import chunks
from io import StringIO
from collections import OrderedDict, Counter
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

class Cut(Base):
  def xform(self, inp):
    return inp[self.select_columns(inp, self.args)]

  def select_columns(self, inp, args):
    selected = []
    for col in args:
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
    return selected

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

class Stats(Base):
  def xform(self, inp):
    out = inp.describe()
    out['stat'] = out.index
    return out
register(Stats, 'stats', ['describe'],
         synopsis="Basic stats of numeric columns.")

class NullXform(Base):
  def xform(self, inp):
    return inp
register(NullXform, 'null', [],
         synopsis="Does nothing.")
