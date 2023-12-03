import pandas as pd
from .command import begin_section, command
from .formats import FormatIn, FormatOut

begin_section('Formats')

@command
class YamlOut(FormatOut):
  '''
  yaml- - Generate YAML.
  alias: yaml, yml-, yml

  :suffix=.yml,.yaml

  Examples:

$ psv in a.csv // yaml

  '''
  def format_out(self, inp, _env, writeable):
    import yaml
    if isinstance(inp, pd.DataFrame):
      rows = inp.reset_index(drop=True).to_dict(orient='records')
      yaml.dump(rows, writeable,
                sort_keys=False,
                default_flow_style=False, allow_unicode=True)
    else:
      raise Exception("yaml-: cannot format {type(inp)}")
