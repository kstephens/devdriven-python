from io import StringIO
import re
import json
import mimetypes
from devdriven.util import not_implemented
import pandas as pd
from devdriven.pandas import format_html
from .command import Command, command
from .content import Content

class FormatIn(Command):
  def xform(self, inp, env):
    if isinstance(inp, pd.DataFrame):
      return inp
    # TODO: reduce(concat,map(FormatIn,map(read, inputs)))
    env['Content-Type'] = 'application/x-pandas-dataframe'
    env['Content-Encoding'] = None
    # TODO: handle streaming:
    if isinstance(inp, str):
      readable = StringIO(inp)
    if isinstance(inp, Content):
      readable = inp.response()
    return self.format_in(readable, env)
  def format_in(self, _io, _env):
    not_implemented()

class FormatOut(Command):
  def xform(self, inp, env):
    self.setup_env(inp, env)
    # TODO: handle streaming:
    out = StringIO()
    self.format_out(inp, env, out)
    return out.getvalue()
  def setup_env(self, _inp, env):
    desc = self.command_descriptor()
    (env['Content-Type'], env['Content-Encoding']) = mimetypes.guess_type('anything' + desc.preferred_suffix)
  def format_out(self, _inp, _env, _writable):
    not_implemented()

############################

@command(preferred_suffix='.txt')
class TableIn(FormatIn):
  '''
  -table - Parse table.
  alias: table-in

  --fs=REGEX       : Field separator.  Default: "\\s+".
  --rs=REGEX       : Record separator.  Default: "\\n\\r?".
  --header, -h     : Headers are in first row.
  --column=FMT     : Column name printf template.  Default: "c%d".
  --encoding=ENC   : Encoding of input.  Default: "utf-8".

  Examples:

# -table: Parse generic table:
$ psv in users.txt // -table --fs=":"

$ psv in users.txt // -table --fs=":" --column='col%02d'

$ psv in us-states.txt // -table --header --fs="\s{2,}" // head 5 // md

  '''
  def format_in(self, readable, _env):
    fs_rx = re.compile(self.opt('fs', r'\s+'))
    rs_rx = re.compile(self.opt('rs', r'\n\r?'))
    column = self.opt('column', 'c')
    if '%' not in column:
      column += '%d'
    skip = self.opt('skip', False)
    skip_rx = skip and re.compile(skip)
    encoding = self.opt('encoding', 'utf-8')
    header = self.opt('header', self.opt('h', False))
    max_width = 0
    # Split content by record separator:
    rows = readable.read()
    if isinstance(rows, bytes):
      rows = rows.decode(encoding)
    rows = re.split(rs_rx, rows)
    # Remove trailing empty record:
    if rows and rows[-1] == '':
      rows.pop(-1)
    # Split row by field separator:
    i = 0
    for row in rows:
      fields = re.split(fs_rx, row)
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
      cols = generate_columns(column, max_width)
    return pd.DataFrame(columns=cols, data=rows)

def generate_columns(column_format, width):
  return map(lambda i: column_format % i, range(1, width + 1))

@command()
class TableOut(FormatOut):
  '''
  table- - Generate table.

  NOT IMPLEMENTED

  :preferred_suffix: .txt
  '''
  def format_out(self, inp, _env, writeable):
    not_implemented()

@command()
class TsvIn(FormatIn):
  '''
  -tsv - Parse TSV.

  :preferred_suffix=.tsv
  '''
  def format_in(self, readable, _env):
    return pd.read_table(readable, sep='\t', header=0)

@command()
class TsvOut(FormatOut):
  '''
  tsv- - Generate TSV.

  :preferred_suffix=.tsv
  '''
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, sep='\t', header=True, index=False, date_format='iso')

@command()
class CsvIn(FormatIn):
  '''
  -csv - Parse CSV.

# csv, json: Convert CSV to JSON:
$ psv in a.csv // -csv // json-

  :preferred_suffix=.csv
  '''
  def format_in(self, readable, _env):
    return pd.read_table(readable, sep=',', header=0)

@command()
class CsvOut(FormatOut):
  '''
  csv- - Generate CSV.

  :preferred_suffix=.csv

  Examples:

# tsv, csv: Convert TSV to CSV:
$ psv in a.tsv // -tsv // csv-

  '''
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, header=True, index=False, date_format='iso')

@command()
class MarkdownOut(FormatOut):
  '''
  md - Generate Markdown.
  aliases: md-, markdown

  :preferred_suffix=.md
  '''
  def content_type(self):
    return 'text/markdown'
  def format_out(self, inp, _env, writeable):
    inp.to_markdown(writeable, index=False)
    # to_markdown doesn't terminate last line:
    writeable.write('\n')

@command()
class JsonIn(FormatIn):
  '''
  -json - Parse JSON.
  --orient=ORIENT : Orientation: see pandas read_json.

  :preferred_suffix=.json
  '''
  def format_in(self, readable, _env):
    orient = self.opt('orient', 'records')
    return pd.read_json(readable, orient=orient)

@command()
class JsonOut(FormatOut):
  '''
  json- - Generate JSON array of objects.
  aliases: json, js-

  :preferred_suffix: .tsv
  '''
  def format_out(self, inp, _env, writeable):
    if isinstance(inp, pd.DataFrame):
      inp.to_json(writeable, orient='records', date_format='iso', index=False, indent=2)
    else:
      json.dump(inp, writeable, indent=2)
    # to_json doesn't terminate last line:
    writeable.write('\n')

@command()
class HtmlOut(FormatOut):
  '''
  html- - Generate HTML.
  alias: html
  --table-name=NAME : <title>
  --header          : Generate header. Default: True.

  :preferred_suffix=.html

  Examples:

# html: Generate HTML:
$ psv in users.txt // -table --header --fs=":" // html // o /tmp/users.html
$ w3m -dump /tmp/users.html

  '''
  def format_out(self, inp, _env, writeable):
    if isinstance(inp, pd.DataFrame):
      opts = {
        'table_name': self.opt('table_name', None),
        'header': bool(self.opt('header', True)),
      }
      format_html(inp, writeable, **opts)
      writeable.write('\n')
    else:
      raise Exception("html-: cannot format {type(inp)}")
