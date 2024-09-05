from typing import Any, Optional
import os
import re
import logging
from pathlib import Path
from datetime import datetime
from collections import OrderedDict
import subprocess
import pandas as pd  # type: ignore
from .util import reorder_list
from .html import Table

def column_type_names(dframe):
  return {col: str(dtype) for col, dtype in dframe.dtypes.to_dict().items()}

def dtype_to_dict(dtype: Any) -> dict:
  return {k: getattr(dtype, k, None) for k in DTYPE_ATTRS}


DTYPE_ATTRS = [
  'name',
  'kind',
  'char',
  'num',
  'str',
  'itemsize',
  'byteorder',
  'subdtype',
  'shape',
  'hasobject',
  'flags',
  'isbuiltin',
  'isnative',
  'descr',
  'alignment',
  'base',
  'metadata',
]

def select_rows(rows, match):
  selected = rows.loc[match]
  selected = selected.reset_index(drop=True)
  selected.drop(['level_0', 'index'], axis=0, errors='ignore', inplace=True)
  selected.drop(['level_0', 'index'], axis=1, errors='ignore', inplace=True)
  return selected

def new_empty_df_like(other):
  # https://stackoverflow.com/a/39174024/1141958
  df = pd.DataFrame().reindex_like(other)
  df.drop(df.index, inplace=True)
  # df = df.iloc[0:0]
  return df

def normalize_column_name(name: str) -> str:
  def decamel(m):
    return f'{m[1]}_{m[2]}'.lower()
  name = re.sub(r'([^A-Z]+)([A-Z]+)', decamel, name)
  return re.sub(r'(?i)[^A-Z0-9]', '_', name)

def push_row(dframe, row):
  dframe.loc[len(dframe)] = row
  return dframe


agg_fun_aliases = {
  'count': 'size',
  'avg': 'mean',
  'total': 'sum',
  'variance': 'var',
  'stddef': 'std',
  'kurtosis': 'kurt',
  'q': 'quantile',
  'r': 'rank',
}

def count_by(df, by, name='count', sort_by=None, sort_ascending=None):
  return summary_by(df, by, None, 'size', name, sort_by, sort_ascending)

# pylint: disable-next=too-many-arguments
def summary_by(df, by, val_col, fun, name, sort_by=None, sort_ascending=None):
  group = df.groupby(by)
  if val_col:
    group = group[val_col]
  df = getattr(group, agg_fun_aliases.get(fun, fun))()
  df = df.reset_index(name=name)
  if sort_by is not None or sort_ascending is not None:
    sort_by = sort_by or name
    sort_ascending = sort_ascending is not False
    df = df.sort_values(sort_by, ascending=sort_ascending)
  remove_index(df)
  return df

# pylint: disable-next=too-many-arguments
def summarize(dframe, col_agg_funs, group_by=None, rename=None, sort_by=None, sort_ascending=True, cols_to_end=None):
  cols = list(map(lambda x: x[0], col_agg_funs))
  aggs = summary_aggs(col_agg_funs)
  if group_by:
    summary = dframe[group_by + cols].groupby(group_by).agg(**aggs)
  else:
    if not cols:
      cols = list(dframe.columns)
    summary = dframe[cols].agg(**aggs).transpose()
  summary.reset_index(inplace=True)
  if rename:
    summary.rename(columns=rename)
  if sort_by:
    summary.sort_values(by=sort_by, ascending=sort_ascending, inplace=True)
  if cols_to_end:
    summary = reorder_cols(summary, back=cols_to_end)
  return summary

def summary_aggs(col_agg_funs):
  aggs = OrderedDict()
  for col, funs in col_agg_funs:
    for fun in funs:
      agg_col = f'{col}_{fun}'
      aggs[agg_col] = pd.NamedAgg(column=col, aggfunc=agg_fun_aliases.get(fun, fun))
  return aggs

def reorder_cols(dframe, front=None, back=None):
  remove_index(dframe)
  cols = list(dframe.columns)
  new = reorder_list(cols, (front or []), (back or []))
  if cols != new:
    dframe = dframe.reindex(new, axis=1)
#    dframe.reset_index(drop=True, inplace=True)
  return dframe

def remove_index(df):
  df.reset_index(drop=True, inplace=True)
  df.drop(labels=['index'], axis=1, errors='ignore', inplace=True)
  df.drop(labels=['index'], axis=0, errors='ignore', inplace=True)
  return df

#########################################
# I/O:

class DataFrameIO:
  src: str = 'data/src'
  gen: str = 'data/gen'
  processing_log: Optional[pd.DataFrame] = None

  def initialize_log(self):
    self.processing_log = pd.DataFrame(columns=['report', 'file', 'mtime', 'lines', 'bytes', 'now', 'url'])

  def write_logs(self, basename):
    if self.processing_log and not self.processing_log.empty:
      self.processing_log.sort_values(by=['report'], ascending=True, inplace=True)
      self.write_df(self.processing_log, f'00-{basename}-log')

  def read_pickle(self, file, **kwargs):
    return pd.read_pickle(file, compression='xz', **kwargs)

  def read_tsv(self, file, **_kwargs):
    return pd.read_table(file,
                         sep='\t', quotechar='\\',
                         doublequote=False,
                         parse_dates=True, infer_datetime_format=True,
                         float_precision='round_trip',
                         header=0)

  def read_json(self, file, **_kwargs):
    return pd.read_json(file, orient='records', convert_dates=True)

  def write_df(self, dframe, report, dirpath=None, **_kwargs):
    remove_index(dframe)
    file = f'{(dirpath or self.gen)}/{report}'
    msg = f'write_df : {file}.* : {len(dframe)} rows'
    logging.info('###########################################')
    logging.info('%s', f'{msg} : ...')
    logging.info('%s', f'{msg} : columns {dframe.columns!r}')
    logging.info(dframe)
    self.saving_df(self.write_pickle, dframe, report, f'{file}.pickle.xz')
    self.saving_df(self.write_tsv, dframe, report, f'{file}.tsv')
    self.saving_df(self.write_html, dframe, report, f'{file}.html')
    self.saving_df(self.write_json, dframe, report, f'{file}.json')
    self.saving_df(self.write_md, dframe, report, f'{file}.md')
    logging.info('%s', f'{msg} : DONE\n')
    return dframe

  def saving_df(self, fun, dframe, report, file):
    logging.info('%s', f"Saving {file} : ...")
    fun(dframe, file)
    if self.processing_log and dframe is not self.processing_log:
      log_row = self.saving_df_log(report, file)
      push_row(self.processing_log, log_row)
    return file

  def saving_df_log(self, report, file):
    file_name = Path(file).name
    log_row = {
      'report': report,
      'file': file_name,
      'mtime': datetime.fromtimestamp(os.path.getmtime(file)),
      'bytes': os.path.getsize(file),
      # https://stackoverflow.com/questions/9629179/python-counting-lines-in-a-huge-10gb-file-as-fast-as-possible
      'lines': int(subprocess.check_output(['/usr/bin/wc', '-l', file]).split()[0]),
      'now': datetime.now()
    }
    logging.info('%s', f'Saving {file} : {log_row!r}')
    return log_row

  def write_pickle(self, dframe, file, **kwargs):
    dframe.to_pickle(file, compression='xz', **kwargs)

  def write_tsv(self, dframe, file, **_kw):
    dframe.to_csv(file,
                  sep='\t', escapechar='\\',
                  date_format='iso',
                  header=True, index=False)

  def write_json(self, dframe, file, **_kw):
    dframe.to_json(file, orient="records", date_format='iso', indent=2)

  def write_md(self, dframe, file, **kw):
    dframe.to_markdown(file, index=False, **kw)

  def write_html(self, dframe, file, **kwargs):
    with open(file, "w", encoding='utf-8') as output:
      Table(columns=dframe.columns(),
            rows=dframe.as_iterable(),
            options=kwargs,
            output=output).render()
