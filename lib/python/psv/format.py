import sys
from io import StringIO
from pathlib import Path
from devdriven.util import not_implemented
import pandas as pd
from .command import Command, register

class FormatIn(Command):
  def xform(self, inp, _env):
    if isinstance(inp, Path):
      readable = str(inp)
      if readable == '-':
        readable = sys.stdin
    else:
      readable = StringIO(str(inp))
    return self.format_in(readable)
  def format_in(self, _io):
    not_implemented()

class FormatOut(Command):
  def xform(self, inp, _env):
    if self.args:
      file = self.args[0]
      if file == '-':
        file = sys.stdout
      self.format_out(inp, file)
      return None
    out = StringIO()
    self.format_out(inp, out)
    return out.getvalue()
  def format_out(self, _inp, _writable):
    not_implemented()

############################

class TsvIn(FormatIn):
  def format_in(self, readable):
    return pd.read_table(readable, sep='\t', header=0)
register(TsvIn, '-tsv', [],
         synopsis="Parse TSV rows.")

class TsvOut(FormatOut):
  def format_out(self, inp, writeable):
    inp.to_csv(writeable, sep='\t', header=True, index=False, date_format='iso')
register(TsvOut, 'tsv-', [],
         synopsis="Generate TSV rows.")

class CsvIn(FormatIn):
  def format_in(self, readable):
    return pd.read_table(readable, sep=',', header=0)
register(CsvIn, '-csv', [],
         synopsis="Parse CSV rows.")

class CsvOut(FormatOut):
  def format_out(self, inp, writeable):
    inp.to_csv(writeable, header=True, index=False, date_format='iso')
register(CsvOut, 'csv-', [],
        synopsis="Generate CSV rows.")

class MarkdownOut(FormatOut):
  def format_out(self, inp, writeable):
    inp.to_markdown(writeable, index=False)
    # to_markdown doesn't terminate last line:
    writeable.write('\n')
register(MarkdownOut, 'md', ['md-', 'markdown'],
         synopsis="Generate a Markdown table.")

class JsonOut(FormatOut):
  def format_out(self, inp, writeable):
    return inp.to_json(writeable, orient='records', date_format='iso', index=False, indent=2)
register(JsonOut, 'json-', ['json', 'js-'],
        synopsis="Generate JSON array of objects.")
