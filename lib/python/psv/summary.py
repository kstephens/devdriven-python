from devdriven.util import split_flat
from devdriven.pandas import count_by, summarize
from .command import Command, begin_section, command
from .util import get_safe, select_columns

begin_section('Summaries')

@command
class Count(Command):
  '''
  count - Count of unique column values.

  COL ...        |  Columns to group by.  Default: ALL COLUMNS.
  --column=NAME  |  Default: "count"

  # Count the number of transfers by Payer:
  $ psv in transfers.csv // count Payer // md

  # Count the number of transfers from Payer to Payee:
  $ psv in transfers.csv // count Payer,Payee // md

  # Count the number of transfers from Payee:
  $ psv in transfers.csv // count --column=PayeeTransfers Payee // md

  '''
  def xform(self, inp, _env):
    count_col = self.opt('column', 'count')
    cols = list(inp.columns)
    if count_col in cols:
      raise AttributeError(f"--column={count_col!r} conflics with columns {cols!r}")
    group_cols = select_columns(inp, split_flat(self.args, ','), check=True)
    if not group_cols:
      group_cols = list(inp.columns)
    return count_by(inp, group_cols, sort_by=group_cols, name=count_col)

@command
class Summary(Command):
  '''
  summary - Summary of column values.

  COL,... [STAT,...] [GROUP-BY,...]    |  COLs to summarize STATs grouped by GROUP-BY

  COL,...       |  Any numeric columns separated by ",".
  STAT,...      |  One or more of: 'count,sum,min,max,mean,median,std,skew'.  See Pandas "DataFrameGroupBy" documentation.  Default: is all of them.
  GROUP-BY,...  |  Any column not in the COL list.  Default: is all of them.

  # Summary of transfers by Payer and Payee:
  $ psv in transfers.csv // summary Amount '*' Payer,Payee

  # Summary of transfers by Payer:
  $ psv in transfers.csv // summary Amount count,sum Payer

  # Sum of Fee by Payee:
  $ psv in transfers.csv // summary Fee sum Payee

  # Summary of all transfer Ammount and Fee:
  $ psv in transfers.csv // cut Amount,Fee // summary Amount,Fee

  '''
  def xform(self, inp, _env):
    cols = get_safe(self.args, 0, '').split(',')
    cols = select_columns(inp, cols, check=True)
    agg_funs = get_safe(self.args, 1, '')
    if not agg_funs or agg_funs == '*':
      agg_funs = 'count,sum,min,mean,median,std,max,skew'
    agg_funs = agg_funs.split(',')
    group_by = get_safe(self.args, 2, '').split(',')
    group_by = select_columns(inp, group_by, check=True, default_all=True)
    if not group_by:
      group_by = list(inp.columns)
    group_by = [col for col in group_by if col not in cols]
    if not cols:
      cols = [group_by[0]]
    col_agg_funs = [[col, agg_funs] for col in cols]
    return summarize(inp, col_agg_funs, group_by=group_by, sort_by=group_by)
