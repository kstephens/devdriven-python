from pathlib import Path
import sys
from .content import Content
from .command import Command, register

class IoBase(Command):
  def user_agent_headers(self, env):
    return {'Content-Type': env['Content-Type']}

class IoIn(IoBase):
  def xform(self, _inp, env):
    if not self.args:
      self.args.append('-')
    content = Content(uri=self.args[0])
    env['input.paths'] = [self.args[0]]
    return content
register(IoIn, 'in', ['i', '-i'],
         synopsis="Read input.",
         args={"FILE ...": "input files.",
               "-": "denotes stdin"})

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
    return None
register(IoOut, 'out', ['o', 'o-'],
         synopsis="Write output.",
         args={"FILE ...": "output files.",
               "-": "denotes stdout"})
