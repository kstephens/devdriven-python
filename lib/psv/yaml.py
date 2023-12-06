import pandas as pd
from .command import section, command
from .formats import FormatOut

section('Formats')

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
    # pylint: disable-next=import-outside-toplevel
    import yaml
    if isinstance(inp, pd.DataFrame):
      for _ind, row in inp.reset_index(drop=True).iterrows():
        yaml.dump([row.to_dict()], writeable,
                sort_keys=False,
                default_flow_style=False, allow_unicode=True)
    else:
      yaml.dump(inp, writeable,
              sort_keys=False,
              default_flow_style=False, allow_unicode=True)
