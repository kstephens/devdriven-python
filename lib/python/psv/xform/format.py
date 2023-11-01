from .base import Base, register
import sys
from devdriven.util import not_implemented
from io import StringIO
from collections import OrderedDict, Counter
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

class FormatIn(Base):
  def xform(self, inp):
    if isinstance(inp, Path):
      io = str(inp)
      if io == '-':
        io = sys.stdin
    else:
      io = StringIO(str(inp))
    return self.format_in(io)
  def format_in(self, io):
    not_implemented()

class FormatOut(Base):
  def xform(self, inp):
    if self.args:
      file = self.args[0]
      if file == '-':
        file = sys.stdout
      self.format_out(inp, file)
    else:
      out = StringIO()
      self.format_out(inp, out)
      return out.getvalue()
#    kwargs = {
#      header=True, index=False, date_format='iso'
#    }
  def format_out(self, inp, io):
    not_implemented()

############################

class TsvIn(FormatIn):
  def format_in(self, io):
    return pd.read_table(io, sep='\t', header=0)
register(TsvIn, '-tsv', [],
         synopsis="Parse TSV rows.")

class TsvOut(FormatOut):
  def format_out(self, inp, io):
    inp.to_csv(io, sep='\t', header=True, index=False, date_format='iso')
register(TsvOut, 'tsv-', [],
         synopsis="Generate TSV rows.")

class CsvIn(FormatIn):
  def format_in(self, io):
    return pd.read_table(io, sep=',', header=0)
register(CsvIn, '-csv', [],
         synopsis="Parse CSV rows.")

class CsvOut(FormatOut):
  def format_out(self, inp, io):
    inp.to_csv(io, header=True, index=False, date_format='iso')
register(CsvOut, 'csv-', [],
        synopsis="Generate CSV rows.")


class MarkdownOut(FormatOut):
  def format_out(self, inp, io):
    inp.to_markdown(io, index=False)
    # to_markdown doesn't terminate last line:
    io.write('\n')
register(MarkdownOut, 'md', ['md-', 'markdown'],
         synopsis="Generate a Markdown table.")


class JsonOut(FormatOut):
  def format_out(self, inp, io):
    return inp.to_json(io, orient='records', date_format='iso', index=False, indent=2)
register(JsonOut, 'json-', ['json', 'js-'],
        synopsis="Generate JSON array of objects.")

