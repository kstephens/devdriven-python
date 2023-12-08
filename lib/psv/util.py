import re
from tempfile import NamedTemporaryFile
from devdriven.util import get_safe, glob_to_rx
import pandas as pd

def get_columns(cols):
  if isinstance(cols, pd.DataFrame):
    cols = list(cols.columns)
  return cols

def parse_column_and_opt(cols, arg):
  cols = get_columns(cols)
  if m := re.match(r'^([^:]+):(.*)$', arg):
    return parse_col_or_index(cols, m[1]), m[2]
  return parse_col_or_index(cols, arg), None

def select_columns(inp, args, check=False, default_all=False):
  inp_cols = get_columns(inp)
  if not args and default_all:
    return inp_cols
  selected = []
  for col in args:
    action = '+'
    if mtch := re.match(r'^([^:]+):([-+]?)$', col):
      col = mtch.group(1)
      action = mtch.group(2)
    col = parse_col_or_index(inp_cols, col)
    col_rx = glob_to_rx(col)
    cols = [col for col in inp_cols if re.match(col_rx, col)]
    if not check and not cols:
      cols = [col]
    if action == '-':
      selected = [x for x in selected if x not in cols]
    else:
      selected = selected + [x for x in cols if x not in selected]
  if check:
    if unknown := [col for col in selected if col not in inp_cols]:
      raise Exception(f"unknown columns: {unknown!r} : available {inp_cols!r}")
  return selected

def parse_col_or_index(cols, arg, check=False):
  cols = get_columns(cols)
  col = arg
#  if m := re.match(r'^(?:@(-\d+)|@?(\d+))$', arg):
#    i = int(m[1] or m[2])
  if m := re.match(r'^@?(-?\d+)$', arg):
    i = int(m[1])
    if i > 0:
      i = i - 1
    col = get_safe(cols, i)
  if check and not col:
    raise Exception(f"unknown column: {col!r} : available {cols!r}")
  return col

BUF_SIZE = 8192 * 2

def tmp_file_to_writeable(writeable, suffix, fun):
  with NamedTemporaryFile(suffix=suffix) as tmp:
    try:
      fun(tmp.name)
      with open(tmp.name, "rb") as tmp_io:
        while buf := tmp_io.read(BUF_SIZE):
          writeable.write(buf)
    finally:
      tmp.close()

def tmp_file_from_readable(readable, suffix, fun):
  with NamedTemporaryFile(suffix=suffix) as tmp:
    try:
      with open(tmp.name, "wb") as tmp_io:
        while buf := readable.read(BUF_SIZE):
          tmp_io.write(buf)
      return fun(tmp.name)
    finally:
      tmp.close()
