import pandas as pd
# from icecream import ic
from .command import section, command
from .formats import FormatIn, FormatOut

section('Format', 20)

@command
class PickleIn(FormatIn):
  '''
  dataframe-in - Read Pandas Dataframe pickle.
  alias: -dataframe

  :suffixes: .pickle.xz
  '''
  def default_encoding(self):
    return None

  def format_in(self, readable, _env):
    return pd.read_pickle(readable, compression='xz')

@command
class PickleOut(FormatOut):
  '''
  dataframe-out - Write Pandas DataFrame pickle.
  alias: dataframe-, dataframe

  :suffixes: .pickle.xz
  '''
  def default_encoding(self):
    return None

  def setup_env(self, inp, env):
    super().setup_env(inp, env)
    env['Content-Type'] = 'application/x-pandas-dataframe-pickle'

  def format_out(self, inp, _env, writeable):
    inp.to_pickle(writeable, compression='xz')
