from devdriven.util import chunks, split_flat
from devdriven.to_dict import to_dict
from devdriven.pandas import dtype_to_dict
from devdriven.random import uuid

import pandas as pd
from .command import Command, section, command
from .util import parse_column_and_opt

section('Metadata', 60)

@command
class AddSequence(Command):
  '''
  add-sequence - Add a column with a sequence of numbers or random values.
  Aliases: seq

  --column=NAME  |  Default: "__i__".
  --start=START  |  Default: 1.
  --step=STEP    |  Default: 1.
  --uuid         |  Generate a UUID-4.

# add-sequence: add a column with a sequence:
$ psv in a.tsv // seq // md

# add-sequence: start at 0:
$ psv in a.tsv // seq --start=0 // md

# add-sequence: step by 2:
$ psv in a.tsv // seq --step=2 // md

# add-sequence: start at 5, step by -2:
$ psv in a.tsv // seq --start=5 --step=-2 // md

# add-sequence: generate UUIDs:
$ psv in a.tsv // seq --uuid // md

  '''
  def xform(self, inp, env):
    out = inp.copy()
    if self.opt('uuid'):
      self.add_uuid(out, env)
    else:
      self.add_range(out, env)
    return out

  def add_range(self, out, _env):
    col = str(self.arg_or_opt(0, 'column', '__i__'))
    start = int(self.arg_or_opt(1, 'start', 1))
    step = int(self.arg_or_opt(2, 'step', 1))
    seq = range(start, start + len(out) * step, step)
    out[col] = seq
    return out

  def add_uuid(self, out, _env):
    col = str(self.arg_or_opt(0, 'column', '__i__'))
    seq = [uuid() for _i in range(0, len(out))]
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

# rename-columns: rename column 'b' to 'Name':
$ psv in a.tsv // rename b:Name // md
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
class ShowColumns(Command):
  '''
  show-columns - Table of column names and attributes.

See numpy.dtype.

  Aliases: columns, cols

# Column metadata columns:
$ psv in a.tsv // cols // cols // cut name,dtype.name // md

# Column metadata:
$ psv in a.tsv // cols // cut name,dtype.name,dtype.kind,dtype.isnative // md

  '''
  def xform(self, inp, _env):
    return pd.DataFrame.from_records(get_dataframe_info(inp))

def get_dataframe_info(dframe):
  return [get_dataframe_col_info(dframe, col) for col in dframe.columns]

def get_dataframe_col_info(df, col):
  dtype = df[col].dtype
  return {
    'name': col,
  } | {
    f'dtype.{k}': v for k, v in dtype_to_dict(dtype).items()
  }

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
