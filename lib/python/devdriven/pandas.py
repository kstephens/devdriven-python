import os
import re
import logging
from pathlib import Path
from datetime import datetime
from collections import OrderedDict
import subprocess
import pandas as pd
from .util import reorder_list

# pylint: disable=invalid-name
src = 'data/src'
gen = 'data/gen'
processing_log = None

def initialize():
  # pylint: disable=global-statement,invalid-name
  global processing_log
  # pylint: enable=global-statement,invalid-name
  processing_log = pd.DataFrame(columns=['report', 'file', 'mtime', 'lines', 'bytes', 'now', 'url'])

def write_logs(basename):
  # pylint: disable=global-statement,invalid-name
  global processing_log
  # pylint: enable=global-statement,invalid-name
  if not processing_log.empty:
    processing_log.sort_values(by=['report'], ascending=True, inplace=True)
    write_df(processing_log, f'00-{basename}-log')
# pylint: enable=invalid-name

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

def normalize_column_name(name):
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

def read_pickle(file, **kwargs):
  return pd.read_pickle(file, compression='xz', **kwargs)

def read_tsv(file, **_kwargs):
  return pd.read_table(file,
                       sep='\t', quotechar='\\',
                       doublequote=False,
                       parse_dates=True, infer_datetime_format=True,
                       float_precision='round_trip',
                       header=0)

def read_json(file, **_kwargs):
  return pd.read_json(file, orient='records', convert_dates=True)

def write_df(dframe, report, dir=None, **_kwargs):
  remove_index(dframe)
  file = f'{(dir or gen)}/{report}'
  msg = f'write_df : {file}.* : {len(dframe)} rows'
  logging.info('###########################################')
  logging.info('%s', f'{msg} : ...')
  logging.info('%s', f'{msg} : columns {dframe.columns!r}')
  logging.info(dframe)
  saving_df(write_pickle, dframe, report, f'{file}.pickle.xz')
  saving_df(write_tsv, dframe, report, f'{file}.tsv')
  saving_df(write_html, dframe, report, f'{file}.html')
  saving_df(write_json, dframe, report, f'{file}.json')
  saving_df(write_md, dframe, report, f'{file}.md')
  logging.info('%s', f'{msg} : DONE\n')
  return dframe

def saving_df(fun, dframe, report, file):
  logging.info('%s', f"Saving {file} : ...")
  fun(dframe, file)
  log_row = saving_df_log(report, file)
  if dframe is not processing_log:
    push_row(processing_log, log_row)
  return file

def saving_df_log(report, file):
  # pylint: disable-next=global-statement,invalid-name
  # global processing_log
  if not processing_log:
    return file
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

def write_pickle(dframe, file, **kwargs):
  dframe.to_pickle(file, compression='xz', **kwargs)

def write_tsv(dframe, file, **_kw):
  dframe.to_csv(file,
                sep='\t', escapechar='\\',
                date_format='iso',
                header=True, index=False)

def write_json(dframe, file, **_kw):
  dframe.to_json(file, orient="records", date_format='iso', indent=2)

def write_md(dframe, file, **kw):
  dframe.to_markdown(file, index=False, **kw)

def write_html(dframe, file, **kwargs):
  with open(file, "w", encoding='utf-8') as output:
    format_html(dframe, output, **kwargs)

def format_html(dframe, output, **kwargs):
  table_name = kwargs.pop('table_name')
  kwargs = {
    "index": False,
    "na_rep": '',
    # "show_dimensions": False,
    "escape": True,
    "render_links": True,
    "sparsify": False
  } | kwargs
  print(f'''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
<head>
<title>{table_name}</title>
<style>{html_css()}</style>
</head>
<body>
<div>
        ''', file=output)
  dframe = dframe.fillna("")
  dframe.to_html(buf=output, **kwargs)
  print('''
</div>
</body>
</html>
          ''', file=output)

def html_css():
  return '''
h1 {
  text-align: left;
}
body {
  /* width: 110%; */
  background-color: black;
  color: white;
  font-family: Arial, Helvetica, sans-serif;
}
table.dataframe {
  border: none !important;
}
table {
  /* width: 110%; */
  width: 1%;
  border: none;
  /* border-collapse: collapse; */
  position: relative;
}
thead {
  position: sticky;
  top: 0;
}
tr {
  border: none;
  /* border-left: 1px solid rgba(255,255,255,16); */
}
tr:nth-child(odd) {
  background-color: rgba(24,24,24,64);
}
tr:hover {
  border: none;
  background-color: rgba(32,32,64,16);
}
.tsv-header {
  position: sticky;
  left: 0; /* needed for sticky? */
}
th, td {
  /* width: auto; */
  width: 1%;
  padding: 1em;
  white-space: pre;
}
th {
  background-color: rgba(32,32,32,16);
  font-weight: bold;
  border-bottom: 1px solid rgba(128,128,128,16);
  text-align: center;
}
td {
  border: none;
  /* border-right: 1px solid rgba(255,255,255,16); */
}
a {
  text-decoration: none;
  color: inherit;
}
a:hover {
  color: rgba(200,160,160,255);
  text-decoration: underline;
}
'''
