from devdriven.util import chunks, split_flat
from devdriven.to_dict import to_dict
import pandas as pd
from .command import Command, command
from .util import *

@command('add-sequence', ['seq'],
         synopsis="Add a column with a sequence of numbers.",
         args={'column': "defaults to __i__"},
         opts={'start': 'start at: defaults to 1.',
               'step':  'step by: defaults to 1.'})
class AddSequence(Command):
  def xform(self, inp, _env):
    col   = str(self.arg_or_opt(0, 'column', '__i__'))
    start = int(self.arg_or_opt(1, 'start', 1))
    step  = int(self.arg_or_opt(2, 'step', 1))
    seq = range(start, start + len(inp) * step, step)
    out = inp.copy()
    out[col] = seq
    return out

@command('add-columns', ['add'],
         synopsis="Add columns.",
         args={'OLD-NAME NEW-NAME ...': 'Columns to rename.'})
class AddColumns(Command):
  def xform(self, inp, _env):
    return inp.rename(columns=dict(chunks(self.args, 2)))

@command('rename-columns', ['rename'],
         synopsis="Rename columns.",
         args={'OLD-COL:NEW-NAME ...': 'Columns to rename.'})
class RenameColumns(Command):
  def xform(self, inp, _env):
    inp_cols = list(inp.columns)
    args = split_flat(self.args, ',')
    rename = [parse_column_and_opt(inp_cols, arg) for arg in args]
    return inp.rename(columns=dict(rename))

@command('infer-objects', ['infer'],
         synopsis="Infer column types.")
class InferObjects(Command):
  def xform(self, inp, _env):
    return inp.infer_objects()

@command('coerce', ['astype'],
         synopsis="Corece column types.",
         args={'COL:TYPE ...': 'Columns to retype.'})
class Coerce(Command):
  def xform(self, inp, _env):
    out = inp.copy()
    inp_cols = list(inp.columns)
    col_types = [parse_column_and_opt(inp_cols, arg) for arg in split_flat(self.args, ',')]
    for col, typ in col_types:
      fun = getattr(self, f'_convert_to_{typ}')
      out[col] = fun(out[col])
    return out
  def _convert_to_numeric(self, seq):
    return pd.to_numeric(seq, errors='ignore')
  def _convert_to_int(self, seq):
    return pd.to_numeric(seq, downcast='integer', errors='ignore')
  def _convert_to_float(self, seq):
    return pd.to_numeric(seq, downcast='float', errors='ignore')
  def _convert_to_str(self, seq):
    return map(str, vseqals.tolist())
  def _convert_to_datetime(self, seq):
    return pd.to_datetime(seq,
                          errors='ignore',
                          # format='mixed',
                          utc=True)


@command('show-columns', ['columns', 'cols'],
         synopsis="Table of column names and attributes.")
class ShowColumns(Command):
  def xform(self, inp, _env):
    out = get_dataframe_info(inp)
    out.reset_index(inplace=True)
    out['index'] = out.index
    out = out.rename(columns={'features':'name'})
    return out

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

@command('env-', [],
         synopsis="Show env.")
class EnvOut(Command):
  def xform(self, _inp, env):
    env['Content-Type'] = 'application/x-psv-env'
    return to_dict(env)

