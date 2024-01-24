import pandas as pd
# from icecream import ic
from .command import section, command
from .formats import FormatIn, FormatOut

section('Format', 20)

@command
class CsvIn(FormatIn):
  '''
  -csv - Parse CSV.

# csv, json: Convert CSV to JSON:
$ psv in a.csv // -csv // json-

  :suffixes: .csv
  '''
  def format_in(self, readable, _env):
    return pd.read_table(readable, sep=',', header=0)

@command
class CsvOut(FormatOut):
  '''
  csv- - Generate CSV.

# tsv, csv: Convert TSV to CSV:
$ psv in a.tsv // -tsv // csv-

  :suffixes: .csv
  '''
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, header=True, index=False, date_format='iso')
