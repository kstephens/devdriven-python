from devdriven.util import chunks, split_flat
from devdriven.to_dict import to_dict
import pandas as pd
from .command import Command, begin_section, command
from .util import *

begin_section('Metadata')

@command
class AddSequence(Command):
  '''
  add-sequence - Add a column with a sequence of numbers.
  Aliases: seq

  --column=NAME  |  Default: "__i__"
  --start=START  |  Default: 1.
  --step=STEP    |  Default: 1.

# add-sequence (seq): add a column with a sequence:
$ psv in a.tsv // seq // md

# add-sequence (seq): start at 0:
$ psv in a.tsv // seq --start=0 // md

# add-sequence (seq): step by 2:
$ psv in a.tsv // seq --step=2 // md

# add-sequence (seq): start at 5, step by -2:
$ psv in a.tsv // seq --start=5 --step=-2 // md


  '''
  def xform(self, inp, _env):
    col   = str(self.arg_or_opt(0, 'column', '__i__'))
    start = int(self.arg_or_opt(1, 'start', 1))
    step  = int(self.arg_or_opt(2, 'step', 1))
    seq = range(start, start + len(inp) * step, step)
    out = inp.copy()
    out[col] = seq
    return out

class AddColumns(Command):
  '''
  add-columns - Add columns.
  Aliases: add

  OLD-NAME NEW-NAME ...  |  Columns to rename.

  '''
  def xform(self, inp, _env):
    return inp.rename(columns=dict(chunks(self.args, 2)))

@command
class RenameColumns(Command):
  '''
  rename-columns - Rename columns.
  Aliases: rename

  OLD-COL:NEW-NAME ...  |  Columns to rename.

# rename-columns: rename column 'b' to 'B':
$ psv in a.tsv // rename b B // md
  '''
  def xform(self, inp, _env):
    inp_cols = list(inp.columns)
    args = split_flat(self.args, ',')
    rename = [parse_column_and_opt(inp_cols, arg) for arg in args]
    return inp.rename(columns=dict(rename))

@command
class InferObjects(Command):
  '''
  infer-objects - Infer column types.
  Aliases: infer

  '''
  def xform(self, inp, _env):
    return inp.infer_objects()

@command
class Coerce(Command):
  '''
  coerce - Corece column types.
  Aliases: astype

  Arguments:

  COL:TYPE ...  |  Columns to retype.
  '''
  def xform(self, inp, _env):
    inp_cols = list(inp.columns)
    col_types = [parse_column_and_opt(inp_cols, arg) for arg in split_flat(self.args, ',')]
    return self.coerce(inp, col_types)

  def coerce(self, inp, col_types):
    out = inp.copy()
    for col, typ in col_types:
      out[col] = self.coercer(typ)(out[col])
    return out
  def coercer(self, typ):
    return getattr(self, f'_convert_to_{typ}')
  def _convert_to_numeric(self, seq):
    return pd.to_numeric(seq, errors='ignore')
  def _convert_to_int(self, seq):
    return pd.to_numeric(seq, downcast='integer', errors='ignore')
  def _convert_to_float(self, seq):
    return pd.to_numeric(seq, downcast='float', errors='ignore')
  def _convert_to_str(self, seq):
    return map(str, seq.tolist())
  def _convert_to_datetime(self, seq):
    return pd.to_datetime(seq,
                          errors='ignore',
                          # format='mixed',
                          utc=True)

@command
class ShowColumns(Command):
  '''
  show-columns - Table of column names and attributes.

  Aliases: columns, cols

# show-columns: show column metadata:
$ psv in a.tsv // show-columns // md

  '''
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

@command
class EnvOut(Command):
  '''
  env- - Show env.

# env: display proccessing info:
$ psv in a.tsv // show-columns // md // env-

  '''
  def xform(self, _inp, env):
    env['Content-Type'] = 'application/x-psv-env'
    return to_dict(env)
