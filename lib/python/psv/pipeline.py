import shlex
import pandas as pd
from devdriven.util import shorten_string
from .content import Content
from . import command

class Pipeline(command.Command):
  def __init___(self, *args):
    super().__init__(*args)
    self.xforms = []

  def parse_argv(self, argv):
    self.xforms = []
    xform_argv = []
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
        self.parse_xform(xform_argv)
        xform_argv = []
      else:
        xform_argv.append(arg)
    self.parse_xform(xform_argv)
    return self

  def parse_xform(self, argv):
    if argv:
      xform = self.make_xform(argv)
      self.xforms.append(xform)
      return xform
    return None

  def xform(self, inp, env):
    history = env['history']
    xform_output = xform_input = inp
    for xform in self.xforms:
      current = [ describe_datum(xform), None, None ]
      history.append(current)
      xform_input = xform_output
      xform_output = xform.xform(xform_input, env)
      current[1] = describe_datum(xform_output)
      current[2] = env['content_type']
    return xform_output

def describe_datum(datum):
  type_name = datum.__class__.__name__
  if isinstance(datum, command.Command):
    type_name = "Command"
    datum = shlex.join([datum.name] + datum.argv)
  elif isinstance(datum, pd.DataFrame):
    datum = datum.shape
  elif isinstance(datum, Content):
    datum = datum.uri
  elif isinstance(datum, bytes) or isinstance(datum, list) or isinstance(datum, dict):
    datum = f'[{len(datum)}]'
  return f"<< {type_name}: {shorten_string(str(datum), 40)} >>"
