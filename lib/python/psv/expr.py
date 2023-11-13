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

  `row` is bound to the current row.
  Return False, the row is removed.
  Return a Dict, the row is updated.

  Aliases: each

  LOGICAL-STATEMENT ...  : Logical statements

  Examples:

  $ bin/psv in -i a.tsv // eval "c *= 2"
  $ bin/psv in -i a.tsv // eval "return c > 0"
  $ bin/psv in -i a.tsv // eval "return {'a': 5}"

  '''
  def xform(self, inp, env):
    cols = list(inp.columns)
    expr = ';'.join(self.args + ['return None'])
    fun = make_expr_fun(expr, cols)
    out = pd.DataFrame(columns=inp.columns)
    stopped = False
    for ind, row in inp.iterrows():
      def stop():
      row = row.to_dict()
      result = fun(inp, env, out, ind, row)
      if stopped:
        break
      if result is False:
        None
      elif result is True or result is None:
        out.loc[len(out.index)] = row
      elif isinstance(result, dict) :
        out.loc[len(out.index)] = row | result
      else:
        raise Exception("eval: unexpected result : {result!r}")
    return out

@command()
class Select(Command):
  '''
  select - Select rows.

  `row` is bound to the current row.
  When expression is true, the row is selected.

  Aliases: each, select

  LOGICAL-EXPRESSION ...  : Logical expression.

  Examples:

  $ bin/psv in -i a.tsv // select "c *= 2"
  $ bin/psv in -i a.tsv // select "c > 0"

  '''
  def xform(self, inp, env):
    cols = list(inp.columns)
    expr = ';'.join(self.args + ['return None'])
    fun = make_expr_fun(expr, cols)
    out = pd.DataFrame(columns=inp.columns)
    for ind, row in inp.iterrows():
      row = row.to_dict()
      result = fun(inp, env, out, ind, row)
      if result is False:
        break
      elif result == 'BREAK':
        break
      elif result == 'FINISH':
        out.loc[len(out.index)] = row
        break
      out.loc[len(out.index)] = row
    return out

COUNTER=[0]

def make_expr_fun(expr, columns):
  COUNTER[0] += 1
  name = f'_psv_Eval_eval_{os.getpid()}_{COUNTER[0]}'
  expr = f'def {name}(inp, env, out, ind, row):\n  {expr}\n'
  expr = rewrite(expr, columns)
  bindings = globals()
  exec(expr, bindings)
  return bindings[name]

def rewrite(expr: str, columns: list):
  parsed = ast.parse(expr, mode='exec')
  #print(ast.dump(parsed, indent=2))
  #print(ast.unparse(parsed))
  rewriter = RewriteName(columns)
  rewritten= rewriter.visit(parsed)
  #print(ast.dump(rewritten, indent=2))
  unparsed = ast.unparse(rewritten)
  #print(unparsed)
  return unparsed

@dataclass
class RewriteName(ast.NodeTransformer):
  columns: list
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

