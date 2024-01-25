import re
import pandas as pd
# from icecream import ic
from .command import section, command
from .formats import FormatIn, FormatOut

section('Format', 20)

############################

@command
class TableIn(FormatIn):
  r'''
  table-in - Parse table.
  alias: -table

  --fs=REGEX          |  Field separator.  Default: "\\s+".
  --rs=REGEX          |  Record separator.  Default: "\\n\\r?".
  --max-cols=COUNT    |  Maximum columns.  Default: 0.
  --columns=COL1,...  |
  --header, -h        |  Column names are in first row.
  --column=FMT        |  Column name printf template.  Default: "c%d".
  --encoding=ENC      |  Encoding of input.  Default: "utf-8".
  --skip=REGEX        |  Records matching REGEX are skipped.

# -table: Parse generic table:
$ psv in users.txt // -table --fs=':'

# -table: Skip users w/o login:
$ psv in users.txt // -table --fs=':' --skip='.*nologin'

# -table: Generate columns named col01, col02, ...:
$ psv in users.txt // -table --fs=':' --column='col%02d'

# -table: Set column names or generate them:
$ psv in users.txt // -table --fs=':' --columns=login,,uid,gid,,home,shell

# -table: Split fields by 2 or more whitespace chars:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // head 5 // md

# -table: Split 3 fields:
$ psv in users.txt // -table --fs=':' --max-cols=3

  :suffix: .txt
  '''
  # pylint: disable-next=too-many-locals
  def format_in(self, readable, _env):
    fs_rx = re.compile(self.opt('fs', r'\s+'))
    rs_rx = re.compile(self.opt('rs', r'\n\r?'))
    columns = self.opt('columns', '')
    columns = re.split(r' *, *| +', columns) if columns else []
    column_format = self.opt('column', 'c')
    max_cols = int(self.opt('max-cols', 0))
    if '%' not in column_format:
      column_format += '%d'
    encoding = self.opt('encoding', self.default_encoding())
    header = self.opt('header')
    max_width = 0
    # Split content by record separator:
    rows = readable.read()
    if isinstance(rows, bytes) and encoding:
      rows = rows.decode(encoding)
    rows = re.split(rs_rx, rows)
    # Remove trailing empty record:
    if rows and rows[-1] == '':
      rows.pop(-1)
    # Remove invalid rows:
    if skip_rx := self.opt('skip'):
      skip_rx = re.compile(skip_rx)
      rows = [row for row in rows if not re.match(skip_rx, row)]
    #   --keep=REGEX     |  Records matching REGEX are kept.
    # if keep_rx := self.opt('keep'):
    #   keep_rx = re.compile(keep_rx)
    #   rows = [row for row in rows if re.match(keep_rx, row)]
    # Split row by field separator:
    i = 0
    for row in rows:
      fields = re.split(fs_rx, row, maxsplit=max_cols)
      max_width = max(max_width, len(fields))
      rows[i] = fields[:]
      i += 1
    # Pad all rows to max row width:
    pads = [[''] * n for n in range(0, max_width + 1)]
    for row in rows:
      row.extend(pads[max_width - len(row)])
    # Take header off the top,
    # otherwise: generate columns by index:
    if header:
      cols = rows.pop(0)
    else:
      cols = generate_columns(columns, column_format, max_width)
    return pd.DataFrame(columns=cols, data=rows)

def generate_columns(columns, column_format, width):
  if width > len(columns):
    columns = columns + [None] * (width - len(columns))
  return map(lambda i: columns[i] or column_format % (i + 1), range(0, width))

@command
class TableOut(FormatOut):
  '''
  table-out - Generate table.
  alias: table-

  --fs=STR    |  Field separator.  Default: " ".
  --rs=STR    |  Record separator.  Default: "\\n".
  --header    |  Emit header.  Default: True.

  NOT IMPLEMENTED

  :suffixes: .txt
  '''
  def format_out(self, _inp, _env, _writeable):
    not_implemented()
