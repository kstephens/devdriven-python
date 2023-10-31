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

class TsvIn(Base):
  def xform(self, inp):
    if isinstance(inp, Path):
      inp = str(inp)
    else:
      inp = StringIO(str(inp))
    return pd.read_table(inp, sep='\t', header=0)
register(TsvIn, '-tsv')

class TsvOut(Base):
  def xform(self, inp):
    if self.args:
      self.to_tsv(inp, self.args[0])
    else:
      out = StringIO()
      self.to_tsv(inp, out)
      return out.getvalue()
  def to_tsv(self, inp, out):
    return inp.to_csv(out, sep='\t', header=True, index=False)
register(TsvOut, 'tsv-')

class CsvIn(Base):
  def xform(self, inp):
    if isinstance(inp, Path):
      inp = str(inp)
    else:
      inp = StringIO(str(inp))
    return pd.read_table(inp, sep=',', header=0)
register(CsvIn, '-csv')

class CsvOut(Base):
  def xform(self, inp):
    if self.args:
      self.to_csv(inp, self.args[0])
    else:
      out = StringIO()
      self.to_csv(inp, out)
      return out.getvalue()
  def to_csv(self, inp, out):
    return inp.to_csv(out, header=True, index=False)
register(CsvOut, 'csv-')
