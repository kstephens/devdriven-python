from typing import Optional, Union, List
import re
from dataclasses import dataclass, field
from devdriven.util import get_safe, glob_to_rx
import pandas as pd  # type: ignore

HasCols = Union[List[str], pd.DataFrame]
Cols = List[str]

# WORK-IN-PROGRESS

@dataclass
class ArgColumn:
  name: str
  index: int = field(default=-1)
  flag: Optional[str] = field(default=None)
  opts: dict = field(default_factory=dict)

@dataclass
class ArgColumnParser:
  inp_cols: Cols
  selected: List[ArgColumn] = field(default_factory=list)
  check: bool = field(default=False)
  default_all: bool = field(default=False)
  split_arg: Optional[str] = field(default=None)

  def parse_args(self, inp: HasCols, args: List[str]):
    self.inp_cols = get_columns(inp)
    if not args and self.default_all:
      self.inp_cols = self.inp_cols

  def parse_arg(self, _inp: HasCols, args: str):
    if self.split_arg:
      for arg in re.split(self.split_arg, args):
        self.parse_arg_basic(arg)
    else:
      self.parse_arg_basic(args)

  def parse_arg_basic(self, _arg: str):
    assert False


def get_columns(cols: HasCols) -> Cols:
  if isinstance(cols, pd.DataFrame):
    cols = list(cols.columns)
  return cols

def parse_column_and_opt(cols: HasCols, arg):
  cols = get_columns(cols)
  if m := re.match(r'^([^:]+):(.*)$', arg):
    return parse_col_or_index(cols, m[1]), m[2]
  return parse_col_or_index(cols, arg), None

def select_columns(inp: HasCols,
                   args: List[str],
                   check=False,
                   default_all=False) -> Cols:
  inp_cols = get_columns(inp)
  if not args and default_all:
    return inp_cols
  selected: Cols = []
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

def parse_col_or_index(cols: HasCols, arg: str, check=False) -> str:
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
