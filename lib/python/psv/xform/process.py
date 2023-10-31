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
    return inp[self.args]
register(Cut, 'cut')

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
register(Sort, 'sort')

class Grep(Base):
  def xform(self, inp):
    filter = has_filter = None
    # https://stackoverflow.com/a/31076657/1141958
    for col, pat in chunks(self.args, 2):
      # ic(col); ic(pat)
      match = inp[col].str.match(pat)
      if has_filter:
        filter = filter & match
      else:
        filter = match
      has_filter = True
    if has_filter:
      return inp[filter]
    return inp
register(Grep, 'grep')

def chunks(xs, n):
  n = max(1, n)
  return (xs[i:i+n] for i in range(0, len(xs), n))

class AddIndex(Base):
  def xform(self, inp):
    # index_name = ((self.args and self.args[0]) or '__index__')
    out = inp.reset_index()
    # out['__index__'] = out.index
    # out = out.rename(columns={'index': index_name})
    return out
register(AddIndex, 'add-index')

#############
# metadata

class Columns(Base):
  def xform(self, inp):
    out = get_dataframe_info(inp)
    out.reset_index(inplace=True)
    out['index'] = out.index
    out = out.rename(columns={'features':'name'})
    return out
register(Columns, 'cols', 'columns')

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

class Describe(Base):
  def xform(self, inp):
    out = inp.describe()
    out['stat'] = out.index
    # out.reset_index(inplace=True)
    # out = out.rename(columns={'index':'stat'})
    out.reset_index(inplace=True, drop=True)
    return out
register(Describe, 'describe')

