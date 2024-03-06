# from icecream import ic
from .command import section, command
from .formats import FormatIn, FormatOut, read_table_with_header

section('Format', 20)

@command
class CsvIn(FormatIn):
  '''
  csv-in - Parse CSV.
  aliases: -csv

--header  |  First row is header.  Default: True.

# Use first row as header:
$ psv in a.csv // -csv

# Generate arbitrary columns:
$ psv in a.csv // -csv --no-header

# Convert CSV to JSON:
$ psv in a.csv // -csv // json-

  :suffixes: .csv
  '''
  def format_in(self, readable, _env):
    return read_table_with_header(readable,
                                  self.opt('header', True),
                                  sep=',')

@command
class CsvOut(FormatOut):
  '''
  csv-out - Generate CSV.
  aliases: csv-, csv

# tsv, csv: Convert TSV to CSV:
$ psv in a.tsv // -tsv // csv-

  :suffixes: .csv
  '''
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, header=True, index=False, date_format='iso')
