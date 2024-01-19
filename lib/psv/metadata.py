import re
from devdriven.util import chunks, split_flat
from devdriven.to_dict import to_dict
from devdriven.pandas import dtype_to_dict
import pandas as pd
# from icecream import ic
from .command import Command, section, command
from .util import parse_column_and_opt

NS_PER_SEC = 1000 * 1000 * 1000

section('Metadata')

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
    col = str(self.arg_or_opt(0, 'column', '__i__'))
    start = int(self.arg_or_opt(1, 'start', 1))
    step = int(self.arg_or_opt(2, 'step', 1))
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

  TYPES:

  numeric      - to int64 or float64.
  int          - to int64.
  float        - to float64.
  timedelta    - string to timedelta64[ns].
  datetime     - string to datetime.
  second       - string to timedelta64[ns] to float seconds.
  minute       - string to timedelta64[ns] to float minutes.
  hour         - string to timedelta64[ns] to float hours.
  day          - string to timedelta64[ns] to float days.
  '''
  def xform(self, inp, _env):
    inp_cols = list(inp.columns)
    col_types = [parse_column_and_opt(inp_cols, arg) for arg in split_flat(self.args, ',')]
    return self.coerce(inp, col_types)

  def coerce(self, inp, col_types):
    out = inp.copy()
    for col, typ_list in col_types:
      for typ in typ_list.split(':'):
        typ = re.sub(r'-', '_', typ)
        typ = self.coercer_aliases.get(typ, typ)
        out[col] = self.coercer(typ)(out[col], col)
    return out

  def coercer(self, typ):
    return getattr(self, f'_convert_to_{typ}')

  coercer_aliases = {
    'n': 'numeric',
    'i': 'int',
    'f': 'f',
    'timedelta_s': 'timedelta_second',
    'timedelta_sec': 'timedelta_second',
    'sec': 'timedelta_second',
    'timedelta_m': 'timedelta_minute',
    'timedelta_min': 'timedelta_minute',
    'min': 'timedelta_minute',
    'timedelta_h': 'timedelta_hour',
    'hr': 'timedelta_hour',
    'hour': 'timedelta_hour',
    'timedelta_hr': 'timedelta_hour',
    'timedelta_d': 'timedelta_day',
    'day': 'timedelta_day',
  }

  def _convert_to_numeric(self, seq, _col):
    return pd.to_numeric(seq, errors='ignore')

  def _convert_to_int(self, seq, _col):
    return pd.to_numeric(seq, downcast='integer', errors='ignore')

  def _convert_to_float(self, seq, _col):
    return pd.to_numeric(seq, downcast='float', errors='ignore')

  def _convert_to_str(self, seq, _col):
    return map(str, seq.tolist())

  def _convert_to_timedelta(self, seq, _col):
    return pd.to_timedelta(seq, errors='ignore')

  def _convert_to_timedelta_scale(self, seq, col, scale):
    seq = pd.to_timedelta(seq, errors='ignore')
    seq = self._convert_to_float(seq, col)
    seq = seq.apply(lambda x: x / scale)
    return seq

  def _convert_to_timedelta_second(self, seq, col):
    return self._convert_to_timedelta_scale(seq, col, NS_PER_SEC)

  def _convert_to_timedelta_minute(self, seq, col):
    return self._convert_to_timedelta_scale(seq, col, NS_PER_SEC * 60)

  def _convert_to_timedelta_hour(self, seq, col):
    return self._convert_to_timedelta_scale(seq, col, NS_PER_SEC * 60 * 60)

  def _convert_to_timedelta_day(self, seq, col):
    return self._convert_to_timedelta_scale(seq, col, NS_PER_SEC * 60 * 60 * 24)

  def _convert_to_datetime(self, seq):
    return pd.to_datetime(seq,
                          errors='ignore',
                          # format='mixed',
                          utc=True)

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
