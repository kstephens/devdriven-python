import re
import pandas as pd
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

# Convert text data to CSV:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // csv- // o us-states.csv

# -table: Split fields by 2 or more whitespace chars:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // head 5 // md

# -table: Split 3 fields:
$ psv in users.txt // -table --fs=':' --max-cols=3

  :suffix: .txt
  '''
  # pylint: disable-next=too-many-locals
  def format_in(self, readable, _env):
    columns = self.opt('columns', '')
    columns = re.split(r' *, *| +', columns) if columns else []
    skip_fn = None
    if skip_rx := self.opt('skip'):
      skip_rx = re.compile(skip_rx)

      def skip_row(row):
        return re.match(skip_rx, row)
      skip_fn = skip_row
    return parse_rows(
      readable,
      field_sep=self.opt('fs', r'\s+'),
      record_sep=self.opt('rs', r'\n\r?'),
      max_cols=self.opt('max-cols'),
      encoding=self.opt('encoding', self.default_encoding()),
      columns=columns,
      header=self.opt('header'),
      skip=skip_fn,
    )

@command
class TableOut(FormatOut):
  '''
  table-out - Generate table.
  alias: table-

  --fs=STR    |  Field separator.  Default: " ".
  --rs=STR    |  Record separator.  Default: "\\n".
  --header    |  Emit header.  Default: True.

$ psv in a.csv // table-
$ psv in a.csv // table- --fs='|'

  :suffixes: .txt
  '''
  def format_out(self, inp, _env, writeable):
    return format_rows(
      writeable, inp,
      field_sep=self.opt('fs', ' '),
      record_sep=self.opt('rs', '\n'),
      header=self.opt('header', True),
      columns=list(inp.columns),
    )


# pylint: disable-next=too-many-arguments
def format_rows(writeable, inp,
                field_sep=None,
                record_sep=None,
                record_prefix=None,
                record_suffix=None,
                header=True,
                columns=None):

  def format_row(row):
    row = [str(col) for col in row]
    row = field_sep.join(row)
    if record_prefix:
      row = record_prefix + row
    if record_suffix:
      row = row + record_suffix
    row = row + record_sep
    writeable.write(row)

  assert columns
  if header:
    format_row(columns)
  for _ind, row in inp.iterrows():
    format_row([row[col] for col in columns])

# pylint: disable-next=too-many-arguments,disable-next=too-many-locals
def parse_rows(
    readable,
    field_sep=None, record_sep=None,
    max_cols=0,
    columns=None,
    column_format='c',
    encoding=None,
    header=None,
    skip=None):
  field_sep_rx = re.compile(field_sep)
  record_sep_rx = re.compile(record_sep)
  max_cols = int(max_cols or 0)
  columns = columns or []
  if '%' not in column_format:
    column_format += '%d'
  max_width = 0
  # Split content by record separator:
  rows = readable.read()
  if isinstance(rows, bytes) and encoding:
    rows = rows.decode(encoding)
  rows = re.split(record_sep_rx, rows)
  # Remove trailing empty record:
  if rows and rows[-1] == '':
    rows.pop(-1)
  # Remove invalid rows:
  if skip:
    rows = [row for row in rows if not skip(row)]
  #   --keep=REGEX     |  Records matching REGEX are kept.
  i = 0
  for row in rows:
    # Split row by field separator:
    fields = re.split(field_sep_rx, row, maxsplit=max_cols)
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
