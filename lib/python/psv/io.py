import json
import pandas as pd
from devdriven.to_dict import to_dict
from .content import Content
from .command import Command, command, find_format
from .formats import FormatIn

class IoBase(Command):
  def user_agent_headers(self, env):
    return {'Content-Type': env['Content-Type']}

@command()
class IoIn(IoBase):
  '''
  in - Read input.

  Aliases: i, -i

  FILE             |  Read FILE.
  file///FILE      |  Read FILE.
  https?://...     |  GET URL.
  -                |  Read STDIN.

  --infer, -i      |  Infer format from suffix.

# in: read from STDIN:
$ cat a.tsv | psv in -
$ cat a.tsv | psv in

# in: HTTP support:
$ psv in https://tinyurl.com/4sscj338

  :section: I/O
  '''
  def xform(self, _inp, env):
    if not self.args:
      self.args.append('-')
    env['input.paths'] = [self.args[0]]
    content = Content(url=self.args[0])
    format_for_suffix = find_format(self.args[0], FormatIn)
    if self.opt('infer', self.opt('i')) and format_for_suffix:
      content = format_for_suffix().set_main(self.main).xform(content, env)
    return content

@command()
class IoOut(IoBase):
  '''
  out - write output to URLs.
  Aliases: o, o-

  FILE             |  Write FILE.
  file///FILE      |  Write FILE.
  https?://...     |  PUT URL.
  -                |  Write STDOUT.

# out: Convert TSV to CSV and save to a file:
$ psv in a.tsv // -tsv // csv- // out a.csv

  :section: I/O
  '''
  def xform(self, inp, env):
    if inp is None:
      return None
    if not self.args:
      self.args.append('-')
    env['output.paths'] = list(map(str, self.args))
    headers = self.user_agent_headers(env)
    # TODO: streaming:
    if isinstance(inp, str):
      body = inp.encode('utf-8')
    elif isinstance(inp, bytes):
      body = inp
    elif isinstance(inp, Content):
      body = inp.body()
    elif isinstance(inp, pd.DataFrame):
      body = (str(inp) + '\n').encode('utf-8')
    else:
      body = json.dumps(to_dict(inp), indent=2)
    for uri in self.args:
      Content(url=uri).put(body, headers=headers)
    return inp
