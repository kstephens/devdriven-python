import re
import ipaddress
from devdriven.util import split_flat
import pandas as pd
# from icecream import ic
from .command import Command, section, command
from .util import parse_column_and_opt

NS_PER_SEC = 1000 * 1000 * 1000

section('Types', 50)

@command
class Coerce(Command):
  '''
  coerce - Corece column types.
  Aliases: astype

  Arguments:

  COL:TYPE ...  |  Column to coerce to TYPE.

  TYPES:

* `numeric`      - to `int64` or `float64`.
* `int`          - to `int64`.
* `float`        - to `float64`.
* `timedelta`    - string to `timedelta64[ns]`.
* `datetime`     - string to `datetime`.
* `second`       - string to `timedelta64[ns]` to `float` seconds.
* `minute`       - string to `timedelta64[ns]` to `float` minutes.
* `hour`         - string to `timedelta64[ns]` to `float` hours.
* `day`          - string to `timedelta64[ns]` to `float` days.
* `ipaddr`       - string to `ipaddress`.  See python `ipaddress` module.

  Examples:

  $ psv in us-states.csv // shuffle // head 10 // cut State,Population // csv- // o us-states-sample.csv
  $ psv in us-states-sample.csv // sort Population
  $ psv in us-states-sample.csv // coerce Population:int // sort Population

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
    seq = remove_commas(seq)
    return pd.to_numeric(seq, errors='coerce')

  def _convert_to_int(self, seq, _col):
    seq = remove_commas(seq)
    return pd.to_numeric(seq, downcast='integer', errors='coerce')

  def _convert_to_float(self, seq, _col):
    seq = remove_commas(seq)
    return pd.to_numeric(seq, downcast='float', errors='coerce')

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
                          infer_datetime_format=True,
                          utc=True)

  def _convert_to_ipaddr(self, seq, _col):
    def to_ipaddr(val):
      try:
        return ipaddress.ip_address(val)
      except ValueError:
        return None
    return seq.apply(to_ipaddr)

def remove_commas(seq):
  return seq.apply(lambda x: str(x).replace(',', ''))
