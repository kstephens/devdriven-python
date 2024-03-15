from devdriven.html import Table
# from icecream import ic
from .command import section, command
from .formats import FormatOut

section('Format', 20)

@command
class HtmlOut(FormatOut):
  '''
  html-out - Generate HTML.
  alias: html-, html

  --title=NAME       |  Set `<title>` and add a `<div>`.
  --header, -h       |  Add table header.  Default: True.
  --simple, -S       |  Minimal format.
  --filtering, -f    |  Add filtering UI.
  --sorting, -s      |  Add sorting support.
  --row-index, -i    |  Add row index to first column.  Default: False.
  --table-only, -T   |  Render only a `<table>`.
  --styled           |  Add style.  Default: True.

  :suffixes: .html,.htm

  Examples:

$ psv in a.csv // html // o a.html
$ w3m -dump a.html

$ psv in users.txt // -table --fs=":" // html --title=users.txt // o users-with-title.html
$ w3m -dump users-with-title.html

$ psv in users.txt // -table --fs=":" // html --no-header // o users-no-header.html
$ w3m -dump users-no-header.html

$ psv in users.txt // -table --fs=":" // html -fs // o users-with-fs.html
$ w3m -dump users-with-fs.html

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
      'header': True,
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
