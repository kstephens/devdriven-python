from . import command

class Pipeline(command.Command):
  def __init___(self, *args):
    super().__init__(*args)
    self.xforms = []

  def parse_argv(self, argv):
    self.xforms = []
    xform_argv = []
    for arg in argv:
      if arg == '//':
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

  def xform(self, inp, env):
    history = env['history']
    xform_output = xform_input = inp
    for xform in self.xforms:
      current = [[ xform.name, *xform.argv ],
                 None]
      history.append(current)
      xform_input = xform_output
      xform_output = xform.xform(xform_input, env)
      current[1] = xform_output
    return xform_output
