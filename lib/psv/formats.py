from io import StringIO, BytesIO
from devdriven.util import not_implemented
from devdriven.mime import content_type_for_suffixes
import pandas as pd
# from icecream import ic
from .command import Command, section, suffix_list
from .content import Content

section('Format', 20)

class FormatBase(Command):
  def default_encoding(self):
    return 'utf-8'

  def wants_input_file(self):
    return False

  def wants_output_file(self):
    return False

class FormatIn(FormatBase):
  def xform(self, inp, env):
    if isinstance(inp, pd.DataFrame):
      return inp
    # ???: reduce(concat,map(FormatIn,map(read, inputs)))
    env['Content-Type'] = 'application/x-pandas-dataframe'
    env['Content-Encoding'] = None
    # ???: handle streaming:
    if isinstance(inp, str):
      if encoding := self.default_encoding():
        readable = StringIO(inp)
      else:
        readable = BytesIO(inp.decode(encoding))
    if isinstance(inp, Content):
      readable = inp.response()
    return self.format_in(readable, env)

  def format_in(self, _io, _env):
    not_implemented()

class FormatOut(FormatBase):
  def xform(self, inp, env):
    self.setup_env(inp, env)
    # ???: handle streaming:
    if self.default_encoding():
      out = StringIO()
    else:
      out = BytesIO()
    self.format_out(inp, env, out)
    return out.getvalue()

  def setup_env(self, _inp, env):
    desc = self.command_descriptor()
    (env['Content-Type'], env['Content-Encoding']) = content_type_for_suffixes(suffix_list(desc))

  def format_out(self, _inp, _env, _writable):
    not_implemented()
