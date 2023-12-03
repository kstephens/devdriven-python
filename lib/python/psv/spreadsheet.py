from devdriven.util import not_implemented
import pandas as pd
from .command import begin_section, command
from .formats import FormatIn, FormatOut
from .content import Content
from tempfile import NamedTemporaryFile

begin_section('Formats')

@command
class XlsOut(FormatOut):
  '''
  xls- - Generate XLS Spreadsheet.
  alias: xls

  --sheet-name=NAME  |  Sheet name
  --header, -h       |  Generate header.  Default: True.

  :suffix=.xls

  Examples:

$ psv in a.csv // xls // o a.xls
$ file a.xls

# $ psv in a.xls // -xls // csv-

  '''
  def format_out(self, inp, _env, writeable):
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    header = bool(self.opt('header', True))
    index = bool(self.opt('index', False))
    wb = Workbook()
    ws = wb.active
    if isinstance(inp, pd.DataFrame):
      for row in dataframe_to_rows(inp, index=index, header=header):
        ws.append(row)
      with NamedTemporaryFile(suffix=".xls") as tmp:
        try:
          wb.save(tmp.name)
          with open(tmp.name, "rb") as in_io:
            while buf := in_io.read(8192):
              writeable.write(buf)
        finally:
          tmp.close()
    else:
      raise Exception("xls-: cannot format {type(inp)}")
  def default_encoding(self):
    return None
