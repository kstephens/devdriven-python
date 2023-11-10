from io import StringIO
import re
import json
import mimetypes
from devdriven.util import not_implemented
import pandas as pd
from devdriven.pandas import format_html
from .command import Command, command

class FormatIn(Command):
  def xform(self, inp, env):
    if isinstance(inp, pd.DataFrame):
      return inp
    # TODO: reduce(concat,map(FormatIn,map(read, inputs)))
    env['Content-Type'] = 'application/x-pandas-dataframe'
    env['Content-Encoding'] = None
    return self.format_in(StringIO(str(inp)), env)
  def format_in(self, _io, _env):
    not_implemented()

class FormatOut(Command):
  def xform(self, inp, env):
    self.setup_env(inp, env)
    # TODO: handle streaming.
    out = StringIO()
    self.format_out(inp, env, out)
    return out.getvalue()
  def setup_env(self, inp, env):
    desc = self.command_descriptor()
    (env['Content-Type'], env['Content-Encoding']) = mimetypes.guess_type('anything' + desc['preferred_suffix'])
  def format_out(self, _inp, _env, _writable):
    not_implemented()

############################

@command('-table', [],
         synopsis="Parse table.",
         preferred_suffix='.txt')
class TableIn(FormatIn):
  def format_in(self, readable, _env):
    self.fs_rx = re.compile(self.opt('fs', r'\s+'))
    self.rs_rx = re.compile(self.opt('rs', r'\n\r?'))
    skip = self.opt('skip', False)
    self.skip_rx = skip and re.compile(skip)
    self.encoding = self.opt('encoding', 'utf-8')
    self.header = self.opt('header', False)
    return self.parse_records(readable, _env)

  def parse_records(self, readable, _env):
    self.max_width = 0
    def parse_row(row):
      fields = re.split(self.fs_rx, row)
      self.max_width = max(self.max_width, len(fields))
      return fields
    def pad_row(row):
      row.extend(pads[max_width - len(row)])
    rows = re.split(self.rs_rx, readable.read())
    if rows and rows[-1] == '':
      rows.pop(-1)
    rows = [ parse_row(row) for row in rows ]
    max_width = self.max_width
    pads = [[''] * n for n in range(0, max_width + 1)]
    for row in rows:
      pad_row(row)
    if self.header:
      cols = rows.pop(0)
    else:
      cols = map(lambda i: f'c{i}', range(1, max_width + 1))
    return pd.DataFrame(columns=cols, data=rows)

@command('table-', [],
         synopsis="Generate table.",
         preferred_suffix='.txt')
class FsOut(FormatOut):
  def format_out(self, inp, _env, writeable):
    not_implemented()

@command('-tsv', [],
         synopsis="Parse TSV rows.",
         preferred_suffix='.tsv')
class TsvIn(FormatIn):
  def format_in(self, readable, _env):
    return pd.read_table(readable, sep='\t', header=0)

@command('tsv-', [],
         synopsis="Generate TSV rows.",
         preferred_suffix='.tsv')
class TsvOut(FormatOut):
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, sep='\t', header=True, index=False, date_format='iso')

@command('-csv', [],
         synopsis="Parse CSV rows.",
         preferred_suffix='.csv')
class CsvIn(FormatIn):
  def format_in(self, readable, _env):
    return pd.read_table(readable, sep=',', header=0)

@command('csv-', [],
        synopsis="Generate CSV rows.",
        preferred_suffix='.csv')
class CsvOut(FormatOut):
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, header=True, index=False, date_format='iso')

@command('md', ['md-', 'markdown'],
         synopsis="Generate a Markdown table.",
         preferred_suffix='.md')
class MarkdownOut(FormatOut):
  def content_type(self):
    return 'text/markdown'
  def format_out(self, inp, _env, writeable):
    inp.to_markdown(writeable, index=False)
    # to_markdown doesn't terminate last line:
    writeable.write('\n')

@command('-json', [],
         synopsis="Parse JSON.",
         preferred_suffix='.json')
class JsonIn(FormatIn):
  def format_in(self, readable, _env):
    orient = self.opt('orient', 'records')
    return pd.read_json(readable, orient=orient)

@command('json-', ['json', 'js-'],
        synopsis="Generate JSON array of objects.",
        preferred_suffix='.tsv')
class JsonOut(FormatOut):
  def format_out(self, inp, _env, writeable):
    if isinstance(inp, pd.DataFrame):
      inp.to_json(writeable, orient='records', date_format='iso', index=False, indent=2)
    else:
      json.dump(inp, writeable, indent=2)
    # to_json doesn't terminate last line:
    writeable.write('\n')

@command('html-', ['html'],
        synopsis="Generate HTML.",
        preferred_suffix='.html')
class HtmlOut(FormatOut):
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
