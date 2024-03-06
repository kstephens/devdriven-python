import json
import pandas as pd
# from icecream import ic
from .command import section, command
from .formats import FormatIn, FormatOut

section('Format', 20)

@command
class JsonIn(FormatIn):
  '''
  json-in - Parse JSON.
  aliases: -json, -js

  --orient=ORIENT  |  Orientation: see pandas read_json.

  :suffixes: .json
  '''
  def format_in(self, readable, _env):
    orient = self.opt('orient', 'records')
    return pd.read_json(readable, orient=orient, convert_dates=True)

@command
class JsonOut(FormatOut):
  '''
  json-out - Generate JSON array of objects.
  aliases: json-, json, js-, js

# csv, json: Convert CSV to JSON:
$ psv in a.csv // -csv // json-

  :suffixes: .json
  '''
  def format_out(self, inp, _env, writeable):
    if isinstance(inp, pd.DataFrame):
      inp.to_json(writeable, orient='records', date_format='iso', index=False, indent=2)
    else:
      json.dump(inp, writeable, indent=2)
    # to_json doesn't terminate last line:
    writeable.write('\n')
