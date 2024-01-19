from io import StringIO, BytesIO
import re
import json
from devdriven.util import not_implemented
from devdriven.mime import content_type_for_suffixes
from devdriven.html import Table
import tabulate
import pandas as pd
# from icecream import ic
from .command import Command, section, command
from .content import Content

section('Formats')

class FormatIn(Command):
  def xform(self, inp, env):
    if isinstance(inp, pd.DataFrame):
      return inp
    # ???: reduce(concat,map(FormatIn,map(read, inputs)))
    env['Content-Type'] = 'application/x-pandas-dataframe'
    env['Content-Encoding'] = None
    # ???: handle streaming:
    if isinstance(inp, str):
      if encoding := self.default_encoding():
        readable = StringIO(inp)
      else:
        readable = BytesIO(inp.decode(encoding))
    if isinstance(inp, Content):
      readable = inp.response()
    return self.format_in(readable, env)

  def default_encoding(self):
    return 'utf-8'

  def format_in(self, _io, _env):
    not_implemented()

class FormatOut(Command):
  def xform(self, inp, env):
    self.setup_env(inp, env)
    # ???: handle streaming:
    if self.default_encoding():
      out = StringIO()
    else:
      out = BytesIO()
    self.format_out(inp, env, out)
    return out.getvalue()

  def setup_env(self, _inp, env):
    desc = self.command_descriptor()
    (env['Content-Type'], env['Content-Encoding']) = content_type_for_suffixes(desc.suffix_list)

  def default_encoding(self):
    return 'utf-8'

  def format_out(self, _inp, _env, _writable):
    not_implemented()

############################

@command
class TableIn(FormatIn):
  r'''
  -table - Parse table.
  alias: table-in

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
    header = self.opt(('header', 'h'))
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
  table- - Generate table.
  alias: table-out

  NOT IMPLEMENTED

  :suffixes: .txt
  '''
  def format_out(self, _inp, _env, _writeable):
    not_implemented()

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

@command
class MarkdownOut(FormatOut):
  '''
  markdown - Generate Markdown.
  aliases: md, md-, markdown-

# md: Convert TSV on STDIN to Markdown:
$ cat a.tsv | psv -tsv // md

  :suffixes: .md,.markdown
  '''
  def format_out(self, inp, _env, writeable):
    tabulate.PRESERVE_WHITESPACE = True
    inp.to_markdown(writeable, index=False)
    # to_markdown doesn't terminate last line:
    writeable.write('\n')

@command
class JsonIn(FormatIn):
  '''
  -json - Parse JSON.

  --orient=ORIENT  |  Orientation: see pandas read_json.

  :suffixes: .json
  '''
  def format_in(self, readable, _env):
    orient = self.opt('orient', 'records')
    return pd.read_json(readable, orient=orient, convert_dates=True)

@command
class JsonOut(FormatOut):
  '''
  json- - Generate JSON array of objects.
  aliases: json, js-

# csv, json: Convert CSV to JSON:
$ psv in a.csv // -csv // json-

  :suffixes: .tsv
  '''
  def format_out(self, inp, _env, writeable):
    if isinstance(inp, pd.DataFrame):
      inp.to_json(writeable, orient='records', date_format='iso', index=False, indent=2)
    else:
      json.dump(inp, writeable, indent=2)
    # to_json doesn't terminate last line:
    writeable.write('\n')

@command
class PickleIn(FormatIn):
  '''
  -pickle - Read Pandas Dataframe pickle.
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
  pickle- - Write Pandas DataFrame pickle.
  alias: dataframe-

  :suffixes: .pickle.xz
  '''
  def default_encoding(self):
    return None

  def setup_env(self, inp, env):
    super().setup_env(inp, env)
    env['Content-Type'] = 'application/x-pandas-dataframe-pickle'

  def format_out(self, inp, _env, writeable):
    inp.to_pickle(writeable, compression='xz')

@command
class HtmlOut(FormatOut):
  '''
  html- - Generate HTML.
  alias: html

  --title=NAME       |  <title>
  --styled           |  Add style.
  --filtering        |  Add filtering UI.
  --sorting          |  Add sorting support.
  --row-index        |  Add row index to first column.
  --table-only       |  Do not render entire HTML document.

  :suffixes: .html,.htm

  Examples:

$ psv in a.csv // html // o a.html
$ w3m -dump a.html

$ psv in users.txt // -table --fs=":" // html // o /tmp/users.html
$ w3m -dump /tmp/users.html

# html: Generate HTML:
$ psv in users.txt // -table --fs=":" // html --no-header // o /tmp/users.html
$ w3m -dump /tmp/users.html

  '''
  def format_out(self, inp, _env, writeable):
    columns = inp.columns
    rows = inp.to_dict(orient='records')
    column_opts = {}
    for col in columns:
      col_opts = column_opts[col] = {}
      dtype = inp[col].dtype
      if dtype.kind in ('i', 'f'):
        col_opts['numeric'] = True
        col_opts['type'] = dtype.name
    opts = {k.replace('-', '_'): v for k, v in self.opts.items()}
    options = {
      'columns': column_opts,
      # 'simple': True,
      'styled': True,
      # 'table_only': True,
      # 'row_ind': True,
    } | opts
    table = Table(
      columns=columns,
      rows=rows,
      options=options,
      output=writeable,
    )
    table.render()

@command
class SQLOut(FormatOut):
  '''
  sql- - Write SQL.
  alias: sql

# sql: Convert TSV to SQL schema:
$ psv in a.tsv // sql

  :suffixes: .sql
  '''
  def format_out(self, inp, _env, writeable):
    # https://stackoverflow.com/a/31075679/1141958
    # https://stackoverflow.com/a/51294670/1141958
    action = self.opt('action', 'create-table')
    table_name = self.opt('table', '__table__')
    if action == 'create-table':
      sql = pd.io.sql.get_schema(inp.reset_index(), table_name)
    writeable.write(sql)
