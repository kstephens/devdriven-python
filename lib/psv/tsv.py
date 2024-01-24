import pandas as pd
# from icecream import ic
from .command import section, command
from .formats import FormatIn, FormatOut

section('Format', 20)

@command
class TsvIn(FormatIn):
  '''
  -tsv - Parse TSV.

# -tsv, csv: Convert TSV to CSV:
$ cat a.tsv | psv -tsv // csv-

# -tsv, md: Convert TSV to Markdown:
$ psv in a.tsv // md

# -tsv: Convert HTTP TSV content to Markdown.
$ psv in https://tinyurl.com/4sscj338 // -tsv // md

  :suffixes: .tsv
  '''
  def format_in(self, readable, _env):
    return pd.read_table(readable, sep='\t', header=0)

@command
class TsvOut(FormatOut):
  '''
  tsv- - Generate TSV.

  :suffixes: .tsv
  '''
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, sep='\t', header=True, index=False, date_format='iso')
