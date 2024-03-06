# from icecream import ic
from .command import section, command
from .formats import FormatIn, FormatOut, read_table_with_header

section('Format', 20)

@command
class TsvIn(FormatIn):
  '''
  tsv-in - Parse TSV.
  aliases: -tsv

--header  |  First row is header.  Default: True.

# Convert TSV stdin to CSV stdout:
$ cat a.tsv | psv -tsv // csv-

# Convert TSV to Markdown:
$ psv in a.tsv // md

# Convert HTTP TSV content to Markdown:
$ psv in https://tinyurl.com/4sscj338 // -tsv // md

  :suffixes: .tsv
  '''
  def format_in(self, readable, _env):
    return read_table_with_header(readable,
                                  self.opt('header', True),
                                  sep='\t')

@command
class TsvOut(FormatOut):
  '''
  tsv-out - Generate TSV.
  aliases: tsv-

# Convert CSV to TSV:
$ psv in a.csv // tsv-

  :suffixes: .tsv
  '''
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, sep='\t', header=True, index=False, date_format='iso')
