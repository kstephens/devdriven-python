import re
import pandas as pd
from devdriven.util import not_implemented
from .content import Content
from .command import Command, command
from .util import *

@command('extract', ['rx', 're'],
         synopsis="Extract fields by Regexp.",
         args={
           },
         opts={
               })
class Extract(Command):
  def xform(self, inp, _env):
    rx = self.args[0]
    rx = re.compile(rx)
    unnamed = self.opt('unnamed', False)
    if unnamed is True:
      unnamed = 'c%d'
    cols, inds = columns_for_rx(rx, unnamed)
    if isinstance(inp, Content):
      recs = str(inp).splitlines()
    elif isinstance(inp, list):
      recs = inp
    else:
      return not_implemented()
    return extract_rows(rx, cols, inds, recs)

def extract_rows(rx, cols, inds, recs):
  rows = []
  def parse_rec(rec):
    if m := re.match(rx, str(rec)):
      row = [ m.group(i) for i in inds ]
      rows.append(row)
  for rec in recs:
    parse_rec(rec)
  return pd.DataFrame(columns=cols, data=rows)

def columns_for_rx(rx, unnamed):
  if unnamed:
    inds = list(range(1, rx.groups + 1))
    cols = [unnamed % i for i in inds]
    for k, i in rx.groupindex.items():
      cols[i - 1] = k
  else:
    cols, inds = [], []
    for k, i in rx.groupindex.items():
      cols.append(k)
      inds.append(i)
  return cols, inds