import re
import os
import ast
from dataclasses import dataclass
from typing import Any
import pandas as pd
from devdriven.util import not_implemented
from .content import Content
from .command import Command, command
from icecream import ic


@command()
class Eval(Command):
  '''
  eval - Evaluate expression for each row.

  Aliases: each

  `row` is bound to the current row.
  Each column is bound to a variable.

  When expression returns:
    * "BREAK":   all remaining rows (inclusive) are dropped.
    * "FINISH":  all remaining rows are dropped.
    * False:     the row is removed.
    * Dict:      the row is updated and new columns are added.

  LOGICAL-STATEMENT ...  : Logical statements

  $ bin/psv in -i a.tsv // eval "c *= 2"
  $ bin/psv in -i a.tsv // eval "return c > 0"
  $ bin/psv in -i a.tsv // eval "return {'a': 99, 'd': 2}"
  $ bin/psv in -i a.tsv // eval "return {'c': c * 2, 'f': len(d)}"

  '''
  def xform(self, inp, env):
    cols = list(inp.columns)
    fun = make_expr_fun(self.create_expr(), cols)
    out = pd.DataFrame(columns=inp.columns)
    stop = False
    i = 0
    for ind, row in inp.iterrows():
      result = fun(inp, env, out, ind, row, i)
      if result == 'BREAK':
        break
      elif result == 'FINISH':
        self.process_row(inp, row, out, result)
        break
      self.process_row(inp, row, out, result)
    return out

  def create_expr(self):
    return ';'.join(self.args + ['return None'])
  def process_row(self, inp, row, out, result):
    if result is True or result is None:
      out.loc[len(out)] = row
    elif isinstance(result, dict):
      row = row.to_dict()
      new_row = row | result
      if len(new_row) > len(row):
        cols = list(out.columns)
        for col in [col for col in new_row.keys() if col not in cols]:
          out.insert(len(cols), col, None)
      out.loc[len(out)] = new_row

@command()
class Select(Eval):
  '''
  select - Select rows.

  When expression is:
  True, the row is selected.

  Aliases: where

  LOGICAL-EXPRESSION ...  : Logical expression.

  $ psv in -i a.tsv // select "c > 0"

  '''
  def create_expr(self):
    return ';'.join(self.args[0:-2] + ['return ' + self.args[-1]])
  def process_row(self, _inp, row, out, result):
    if result:
      out.loc[len(out)] = row

COUNTER=[0]

def make_expr_fun(expr, columns):
  COUNTER[0] += 1
  name = f'_psv_Eval_eval_{os.getpid()}_{COUNTER[0]}'
  expr = f'def {name}(inp, env, out, ind, row, i):\n  {expr}\n'
  expr = rewrite(expr, columns)
  bindings = globals()
  exec(expr, bindings)
  return bindings[name]

def rewrite(expr: str, columns: list):
  parsed = ast.parse(expr, mode='exec')
  rewriter = RewriteName(columns)
  rewritten= rewriter.visit(parsed)
  return ast.unparse(rewritten)

@dataclass
class RewriteName(ast.NodeTransformer):
  columns: list
  # pylint: disable-next=invalid-name
  def visit_Name(self, node):
    if node.id in self.columns:
      return ast.Subscript(
        value=ast.Name(id='row', ctx=ast.Load()),
        slice=ast.Constant(value=node.id),
        ctx=node.ctx
      )
    else:
      return node


@command()
class PdEval(Command):
  '''
  pd-eval - pandas.DataFrame.eval.

  $ bin/psv in -i a.tsv // pd-eval "c *= 2"

  '''
  def xform(self, inp, _env):
    out = inp.eval(self.args[0],
            **self.opts_kwargs({'parser': 'pandas',
                                'engine': None,
                               }))
    return out

  def opts_kwargs(self, spec):
    return {name: self.opt(name, default)
            for name, default in spec.items()}

