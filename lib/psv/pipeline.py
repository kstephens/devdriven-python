import shlex
import pandas as pd
from devdriven.util import shorten_string, get_safe
from .content import Content
from . import command

class Pipeline(command.Command):
  def __init__(self, *args):
    super().__init__(*args)
    self.xforms = []

  def parse_argv(self, argv):
    self.xforms = []
    xform_argv = []

    def parse_xform(argv):
      if argv:
        xform = self.make_xform(argv)
        self.xforms.append(xform)
        return xform
      return None

    depth = 0
    for arg in argv:
      if arg == '{{':
        depth += 1
        xform_argv.append(arg)
      elif arg == '}}':
        depth -= 1
        xform_argv.append(arg)
      elif depth > 0:
        xform_argv.append(arg)
      elif arg == '//':
        parse_xform(xform_argv)
        xform_argv = []
      else:
        xform_argv.append(arg)
    parse_xform(xform_argv)
    return self

  def xform(self, inp, env):
    history = env['history']
    xform_output = xform_input = inp
    i = 0
    for xform in self.xforms:
      current = [describe_datum(xform), None, None, None]
      history.append(current)
      xform_input = xform_output
      try:
        env['xform'].update({
          'first': get_safe(self.xforms, 0),
          'last': get_safe(self.xforms, -1),
          'prev': get_safe(self.xforms, i - 1),
          'next': get_safe(self.xforms, i + 1),
          'current': current,
        })
        xform_output = xform.xform(xform_input, env)
      except Exception as exc:
        self.log('error', '%s', f'{exc}')
        raise exc
      #  raise Exception(f'{xform.name} : {exc}') from exc
      current[1] = describe_datum(xform_output)
      current[2] = env['Content-Type']
      current[3] = env['Content-Encoding']
    return xform_output

def describe_datum(datum):
  type_name = datum.__class__.__name__
  if isinstance(datum, command.Command):
    type_name = datum.__class__.__name__
    datum = shlex.join([datum.name] + datum.argv)
  elif isinstance(datum, pd.DataFrame):
    datum = datum.shape
  elif isinstance(datum, Content):
    datum = datum.url
  elif isinstance(datum, (bytes, list, dict)):
    datum = f'[{len(datum)}]'
  return f"<< {type_name}: {shorten_string(str(datum), 40)} >>"
