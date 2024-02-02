import json
import pandas as pd
# from icecream import ic
from devdriven.to_dict import to_dict
from .content import Content
from .command import Command, command, section, find_format
from .formats import FormatIn

section('I/O', 10)

class IoBase(Command):
  def user_agent_headers(self, env):
    return {'Content-Type': env['Content-Type']}

@command
class IoIn(IoBase):
  '''
  in - Read input.

  Aliases: i, -i

If no arguments are given, read from STDIN.

  FILE             |  Read FILE.
  file:///FILE     |  Read FILE.
  https?://URL     |  GET URL.
  -                |  Read STDIN.

  --auto, -a       |  Attempt to infer format from suffix.
  --raw, -r        |  Do not attempt infer format.

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
    content = Content(url=self.args[0],
                      stdin=self.main.stdin,
                      stdout=self.main.stdout)
    infer = True
    infer = infer or self.opt('auto', False)
    infer = infer and not self.next_xform_is_format_in(env)
    infer = infer and not self.opt('raw', False) and not content.is_stdio()
    format_for_suffix = infer and find_format(self.args[0], FormatIn)
    if infer and format_for_suffix:
      xform = format_for_suffix()
      xform.main = self.main
      xform.opts = self.opts
      content = xform(content, env)
    return content

  def next_xform_is_format_in(self, env: dict):
    return issubclass(type(env['xform']['next']), FormatIn)


@command
class IoOut(IoBase):
  '''
  out - write output to URLs.
  Aliases: o, o-

If no arguments are given, write to STDOUT.

  FILE             |  Write FILE.
  file///FILE      |  Write FILE.
  https?://...     |  PUT URL.
  -                |  Write STDOUT.

--encoding=ENC     |  Use encoding.  Default: 'UTF-8'.

# out: Convert TSV to CSV and save to a file:
$ psv in a.tsv // -tsv // csv- // out a.csv

  :section: I/O
  '''
  def xform(self, inp, env):
    if inp is None:
      return None
    if not self.args:
      self.args.append('-')
    encoding = self.opt('encoding', 'UTF-8')
    env['output.paths'] = list(map(str, self.args))
    # ???: handle encoding header?
    headers = self.user_agent_headers(env)
    # ???: implement streaming:
    if isinstance(inp, str):
      body = inp.encode(encoding)
    elif isinstance(inp, bytes):
      body = inp
    elif isinstance(inp, Content):
      body = inp.body()
    elif isinstance(inp, pd.DataFrame):
      body = (str(inp) + '\n').encode(encoding)
    else:
      body = json.dumps(to_dict(inp), indent=2)
    for uri in self.args:
      Content(url=uri,
              stdin=self.main.stdin,
              stdout=self.main.stdout).put(body, headers=headers)
    return inp
