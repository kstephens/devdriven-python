from .content import Content
from .command import Command, command, find_format
from .format import FormatIn

class IoBase(Command):
  def user_agent_headers(self, env):
    return {'Content-Type': env['Content-Type']}

@command('in', ['i', '-i'],
         synopsis="Read input.",
         args={"FILE ...": "input files.",
               "-": "denotes stdin"},
         opts={"--infer, -i":  "Infer format from suffix."})
class IoIn(IoBase):
  def xform(self, _inp, env):
    if not self.args:
      self.args.append('-')
    env['input.paths'] = [self.args[0]]
    content = Content(uri=self.args[0])
    format_for_suffix = find_format(self.args[0], FormatIn)
    if self.opt('infer', self.opt('i')) and format_for_suffix:
      content = format_for_suffix().set_main(self.main).xform(content, env)
    return content

@command('out', ['o', 'o-'],
         synopsis="Write output.",
         args={"FILE ...": "output files.",
               "-": "denotes stdout"})
class IoOut(IoBase):
  def xform(self, inp, env):
    if inp is None:
      return None
    inp = str(inp)
    if not self.args:
      self.args.append('-')
    env['output.paths'] = list(map(str, self.args))
    headers = self.user_agent_headers(env)
    body = inp.encode('utf-8')
    for uri in self.args:
      Content(uri=uri).put_content(body, headers=headers)
    return inp
