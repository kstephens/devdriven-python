from devdriven.util import split_flat
from devdriven.pandas import count_by, summarize
from .command import Command, begin_section, command
from .util import get_safe, select_columns

begin_section('Summaries')

@command
class Count(Command):
  '''
  count - Count of unique column values.

  Arguments:

  COL ...        |  Columns to group by.  Default: ALL COLUMNS.

  Options:

  --column=NAME  |  Default: "__count__"
  '''
  def xform(self, inp, _env):
    count_col = self.opt('column', '__count__')
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
  STAT,...      |  One of: 'count,sum,min,max,mean,median,std,skew'. Default: is all of them.  See Pandas "DataFrameGroupBy" documentation.
  GROUP-BY,...  |  Any column not in the COL list.  Default: is all of them.

  '''
  def xform(self, inp, _env):
    cols = get_safe(self.args, 0, '').split(',')
    cols = select_columns(inp, cols, check=True)
    agg_funs = (get_safe(self.args, 1, '') or 'count,sum,min,mean,median,std,max,skew').split(',')
    group_by = get_safe(self.args, 2, '').split(',')
    group_by = select_columns(inp, group_by, check=True, default_all=True)
    if not group_by:
      group_by = list(inp.columns)
    group_by = [col for col in group_by if col not in cols]
    if not cols:
      cols = [group_by[0]]
    col_agg_funs = [[col, agg_funs] for col in cols]
    # ic(cols)
    # ic(group_by)
    # ic(agg_funs)
    # ic(col_agg_funs)
    return summarize(inp, col_agg_funs, group_by=group_by, sort_by=group_by)
