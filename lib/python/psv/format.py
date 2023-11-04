import sys
from io import StringIO
import json
from pathlib import Path
from devdriven.util import not_implemented
import pandas as pd
from .command import Command, register

class Format(Command):
  def content_type(self):
    return ''

class FormatIn(Format):
  def xform(self, inp, env):
    # TODO: reduce(concat,map(FormatIn,map(read, inputs)))
    if self.args:
      readable = self.args[0]
      if readable == '-':
        readable = sys.stdin
    elif isinstance(inp, Path):
      readable = str(inp)
      if readable == '-':
        readable = sys.stdin
    else:
      readable = StringIO(str(inp))
    env['content_type'] = 'application/x-pandas-dataframe'
    return self.format_in(readable, env)
  def format_in(self, _io, _env):
    not_implemented()

class FormatOut(Format):
  def xform(self, inp, env):
    env['content_type'] = self.content_type()
    if self.args:
      file = self.args[0]
      if file == '-':
        file = sys.stdout
      self.format_out(inp, env, file)
      return None
    out = StringIO()
    self.format_out(inp, env, out)
    # ic(out.getvalue())
    return out.getvalue()
  def format_out(self, _inp, _env, _writable):
    not_implemented()

############################

class TsvIn(FormatIn):
  def format_in(self, readable, _env):
    return pd.read_table(readable, sep='\t', header=0)
register(TsvIn, '-tsv', [],
         synopsis="Parse TSV rows.")

class TsvOut(FormatOut):
  def content_type(self):
    return 'application/csv'
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, sep='\t', header=True, index=False, date_format='iso')
register(TsvOut, 'tsv-', [],
         synopsis="Generate TSV rows.")

class CsvIn(FormatIn):
  def format_in(self, readable, _env):
    return pd.read_table(readable, sep=',', header=0)
register(CsvIn, '-csv', [],
         synopsis="Parse CSV rows.")

class CsvOut(FormatOut):
  def content_type(self):
    return 'application/csv'
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, header=True, index=False, date_format='iso')
register(CsvOut, 'csv-', [],
        synopsis="Generate CSV rows.")

class MarkdownOut(FormatOut):
  def content_type(self):
    return 'text/markdown'
  def format_out(self, inp, _env, writeable):
    inp.to_markdown(writeable, index=False)
    # to_markdown doesn't terminate last line:
    writeable.write('\n')
register(MarkdownOut, 'md', ['md-', 'markdown'],
         synopsis="Generate a Markdown table.")

class JsonIn(FormatIn):
  def format_in(self, readable, _env):
    orient = self.opt('orient', 'records')
    return pd.read_json(readable, orient=orient)
register(JsonIn, '-json', [],
         synopsis="Parse JSON.")

class JsonOut(FormatOut):
  def content_type(self):
    return 'application/json'
  def format_out(self, inp, _env, writeable):
    if isinstance(inp, pd.DataFrame):
      return inp.to_json(writeable, orient='records', date_format='iso', index=False, indent=2)
    else:
      return json.dump(inp, writeable, indent=2)
register(JsonOut, 'json-', ['json', 'js-'],
        synopsis="Generate JSON array of objects.")
