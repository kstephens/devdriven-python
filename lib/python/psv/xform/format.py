from .base import Base, register
import json
import re
import subprocess
import sys
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
    raise Exception("not implemented")

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
  def format_out(self, inp, io):
    raise Exception("not implemented")

############################

class TsvIn(FormatIn):
  def format_in(self, io):
    return pd.read_table(io, sep='\t', header=0)
register(TsvIn, '-tsv')

class TsvOut(FormatOut):
  def format_out(self, inp, io):
    inp.to_csv(io, sep='\t', header=True, index=False, date_format='iso')
register(TsvOut, 'tsv-')

class CsvIn(FormatIn):
  def format_in(self, io):
    return pd.read_table(io, sep=',', header=0)
register(CsvIn, '-csv')

class CsvOut(FormatOut):
  def format_out(self, inp, io):
    inp.to_csv(io, header=True, index=False, date_format='iso')
register(CsvOut, 'csv-')

class MarkdownOut(FormatOut):
  def format_out(self, inp, io):
    inp.to_markdown(io, index=False)
    # to_markdown doesn't terminate last line:
    io.write('\n')
register(MarkdownOut, 'md-', 'markdown', 'md')

class JsonOut(FormatOut):
  def format_out(self, inp, io):
    return inp.to_json(io, orient='records', date_format='iso', index=False, indent=2)
register(JsonOut, 'json-', 'json', 'js-')
