import pandas as pd
# from icecream import ic
from .command import section, command
from .formats import FormatOut

section('Format', 20)

@command
class SQLOut(FormatOut):
  '''
  sql- - Write SQL.
  alias: sql

# sql: Convert TSV to SQL schema:
$ psv in a.tsv // sql

  :suffixes: .sql
  '''
  def format_out(self, inp, _env, writeable):
    # https://stackoverflow.com/a/31075679/1141958
    # https://stackoverflow.com/a/51294670/1141958
    action = self.opt('action', 'create-table')
    table_name = self.opt('table', '__table__')
    if action == 'create-table':
      sql = pd.io.sql.get_schema(inp.reset_index(), table_name)
    writeable.write(sql)
