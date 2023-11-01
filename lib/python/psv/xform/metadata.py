from .base import Base, register
import re
from devdriven.util import chunks
from io import StringIO
from collections import OrderedDict, Counter
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

class AddSequence(Base):
  def xform(self, inp):
    start = int(self.opt('start', 1))
    step  = int(self.opt('step', 1))
    col   = (self.args and self.args[0]) or '__i__'
    out = inp.copy()
    out[col] = range(start, start + len(out) * step, step)
    return out
register(AddSequence, 'add-sequence', ['seq'],
         synopsis="Add a column with a sequence of numbers.",
         args={'NEW-COLUMN': "defaults to __i__"},
         opts={'start': 'start at: defaults to 1.',
               'step':  'step by: defaults to 1.'})

class RenameColumns(Base):
  def xform(self, inp):
    out = inp.rename(columns=dict(chunks(self.args, 2)))
    return out
register(RenameColumns, 'rename-columns', ['rename'],
         synopsis="Rename columns.",
         args={'OLD-NAME NEW-NAME ...': 'Columns to rename.'})

class Columns(Base):
  def xform(self, inp):
    out = get_dataframe_info(inp)
    out.reset_index(inplace=True)
    out['index'] = out.index
    out = out.rename(columns={'features':'name'})
    return out
register(Columns, 'columns', ['cols'],
         synopsis="Table of column names and attributes.")

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

