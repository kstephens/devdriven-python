import yaml
import pandas as pd
from .command import section, command
from .formats import FormatOut

section('Format', 20)

@command
class YamlOut(FormatOut):
  '''
  yaml-out - Generate YAML.
  aliases: yaml-, yaml, yml-, yml

  :suffixes: .yaml, .yml

  Examples:

$ psv in a.csv // yaml

  '''
  def format_out(self, inp, _env, writeable):
    if isinstance(inp, pd.DataFrame):
      for _ind, row in inp.reset_index(drop=True).iterrows():
        yaml.dump([row.to_dict()], writeable,
                  sort_keys=False,
                  default_flow_style=False, allow_unicode=True)
    else:
      yaml.dump(inp, writeable,
                sort_keys=False,
                default_flow_style=False, allow_unicode=True)
