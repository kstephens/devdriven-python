# pylint: disable=unused-import,wildcard-import,redefined-builtin,unused-wildcard-import
import re
import os
import ast
from math import *
from dataclasses import dataclass
import pandas as pd
from devdriven.pandas import new_empty_df_like, normalize_column_name
from .command import Command, section, command
# pylint: enable=unused-import,wildcard-import,redefined-builtin,unused-wildcard-import


section('Expression Evaluation', 70)

@command
class Eval(Command):
  '''
  eval - Evaluate expression for each row.

  Aliases: each

  Variable Bindings:
  Columns are bound to variables:
    * `inp`    : input table.
    * `out`    : output table.
    * `row`    : current row.
    * `ind`    : row index.
    * `offset` : row offset (zero origin).

  When expression returns:
    * "FINISH" : all remaining rows are dropped.
    * "BREAK"  : all remaining rows (inclusive) are dropped.
    * False    : the row is removed.
    * Dict     : the row is updated and new columns are added.

  STATEMENT ...        |  Statements.  Final statement may return a value.

  --columns=COL,...    |  Columns bound within STATEMENT.  Default: input columns.
  --normalize, -n      |  Column bound within STATEMENT are normalized to r'^[a-z0-9_]+$'.  Default: False.

  $ psv in a.tsv // eval "c *= 2"
  $ psv in a.tsv // eval "return c > 0"
  $ psv in a.tsv // eval "return {'i': offset, 'd_length': 2}"
  $ psv in a.tsv // eval "return {'c': c * 2, 'f': len(d)}"
  $ psv in a.tsv // rename d:dCamelCase // eval +n 'dCamelCase *= 2'
  $ psv in a.tsv // rename d:dCamelCase // eval -n 'd_camel_case *= 2'

  '''
  def xform(self, inp, env):
    cols = list(filter(len, self.opt('columns', '').split(','))) or list(inp.columns)
    if self.opt('normalize', False):
      ident_to_column = {normalize_column_name(col): col for col in cols}
    else:
      ident_to_column = dict(zip(cols, cols))
    fun = make_expr_fun(self.create_expr(), ident_to_column)
    out = new_empty_df_like(inp)
    offset = 0
    for ind, row in inp.iterrows():
      result = fun(inp, env, out, ind, row, offset)
      if result == 'BREAK':
        break
      self.process_row(inp, row, out, result)
      if result == 'FINISH':
        break
      offset += 1
    return out

  def create_expr(self):
    return ';'.join(self.args + ['return None'])

  def process_row(self, _inp, row, out, result):
    if result is True or result is None:
      out.loc[len(out)] = row
    # elif isinstance(result, tuple):
    #  col, val = result
    #  out.insert(len(out.columns), col, None)
    #  row[col] = val
    elif isinstance(result, dict):
      row = row.to_dict()
      new_row = row | result
      if len(new_row) > len(out.columns):
        for col in [col for col in result.keys() if col not in out.columns]:
          # self.log('debug', 'inserting %s', repr(col))
          out.insert(len(out.columns), col, None)
      out.loc[len(out)] = new_row

@command
class Select(Eval):
  '''
  select - Select rows.

  Aliases: where

  When expression is True, the row is selected.
  "BREAK" and "FINISH" conditions in `eval` command also apply.

  LOGICAL-EXPRESSION ...  |  Logical expression.

  $ psv in a.tsv // select "c > 0"

  '''
  def create_expr(self):
    return ';'.join(self.args[0:-2] + ['return ' + self.args[-1]])

  def process_row(self, _inp, row, out, result):
    if result:
      out.loc[len(out)] = row


COUNTER = [0]

def make_expr_fun(expr: str, ident_to_column: dict):
  COUNTER[0] += 1
  name = f'_psv_Eval_eval_{os.getpid()}_{COUNTER[0]}'
  expr = f'def {name}(inp, env, out, ind, row, offset):\n  {expr}\n'
  expr = rewrite(expr, ident_to_column)
  bindings = globals()
  # pylint: disable-next=exec-used
  exec(expr, bindings)
  return bindings[name]

def rewrite(expr: str, ident_to_column: dict):
  parsed = ast.parse(expr, mode='exec')
  rewriter = RewriteName(ident_to_column)
  rewritten = rewriter.visit(parsed)
  return ast.unparse(rewritten)

@dataclass
class RewriteName(ast.NodeTransformer):
  ident_to_column: dict

  # pylint: disable-next=invalid-name
  def visit_Name(self, node):
    if col := self.ident_to_column.get(node.id, None):
      return ast.Subscript(
        value=ast.Name(id='row', ctx=ast.Load()),
        slice=ast.Constant(value=col),
        ctx=node.ctx
      )
    return node
