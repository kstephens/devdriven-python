from devdriven.util import chunks
import pandas as pd
from .command import Command, register

class AddSequence(Command):
  def xform(self, inp, _env):
    col   = str(self.arg_or_opt(0, 'column', '__i__'))
    start = int(self.arg_or_opt(1, 'start', 1))
    step  = int(self.arg_or_opt(2, 'step', 1))
    seq = range(start, start + len(inp) * step, step)
    out = inp.copy()
    out[col] = seq
    return out
register(AddSequence, 'add-sequence', ['seq'],
         synopsis="Add a column with a sequence of numbers.",
         args={'column': "defaults to __i__"},
         opts={'start': 'start at: defaults to 1.',
               'step':  'step by: defaults to 1.'})

class RenameColumns(Command):
  def xform(self, inp, _env):
    out = inp.rename(columns=dict(chunks(self.args, 2)))
    return out
register(RenameColumns, 'rename-columns', ['rename'],
         synopsis="Rename columns.",
         args={'OLD-NAME NEW-NAME ...': 'Columns to rename.'})

class Columns(Command):
  def xform(self, inp, _env):
    out = get_dataframe_info(inp)
    out.reset_index(inplace=True)
    out['index'] = out.index
    out = out.rename(columns={'features':'name'})
    return out
register(Columns, 'columns', ['cols'],
         synopsis="Table of column names and attributes.")

def get_dataframe_info(dframe):
  df_types = pd.DataFrame(dframe.dtypes)
  df_nulls = dframe.count()
  df_null_count = pd.concat([df_types, df_nulls], axis=1)
  df_null_count = df_null_count.reset_index()
  # Reassign column names
  col_names = ["features", "types", "non_null_counts"]
  df_null_count.columns = col_names
  # Add this to sort
  # df_null_count = df_null_count.sort_values(by=["null_counts"], ascending=False)
  return df_null_count

