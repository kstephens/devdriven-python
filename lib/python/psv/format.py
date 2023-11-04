import sys
from io import StringIO
import json
from devdriven.util import not_implemented
import pandas as pd
from .command import Command, register
import mimetypes

class FormatIn(Command):
  def xform(self, inp, env):
    # TODO: reduce(concat,map(FormatIn,map(read, inputs)))
    env['Content-Type'] = 'application/x-pandas-dataframe'
    env['Content-Encoding'] = None
    return self.format_in(StringIO(str(inp)), env)
  def format_in(self, _io, _env):
    not_implemented()

class FormatOut(Command):
  def xform(self, inp, env):
    self.setup_env(inp, env)
    # TODO: handle streaming.
    out = StringIO()
    self.format_out(inp, env, out)
    return out.getvalue()
  def setup_env(self, inp, env):
    desc = self.command_descriptor()
    (env['Content-Type'], env['Content-Encoding']) = mimetypes.guess_type('anything' + desc['preferred_suffix'])
  def format_out(self, _inp, _env, _writable):
    not_implemented()

############################

class TsvIn(FormatIn):
  def format_in(self, readable, _env):
    return pd.read_table(readable, sep='\t', header=0)
register(TsvIn, '-tsv', [],
         synopsis="Parse TSV rows.",
         preferred_suffix='.tsv')

class TsvOut(FormatOut):
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, sep='\t', header=True, index=False, date_format='iso')
register(TsvOut, 'tsv-', [],
         synopsis="Generate TSV rows.",
         preferred_suffix='.tsv')

class CsvIn(FormatIn):
  def format_in(self, readable, _env):
    return pd.read_table(readable, sep=',', header=0)
register(CsvIn, '-csv', [],
         synopsis="Parse CSV rows.",
         preferred_suffix='.csv')

class CsvOut(FormatOut):
  def format_out(self, inp, _env, writeable):
    inp.to_csv(writeable, header=True, index=False, date_format='iso')
register(CsvOut, 'csv-', [],
        synopsis="Generate CSV rows.",
        preferred_suffix='.csv')

class MarkdownOut(FormatOut):
  def content_type(self):
    return 'text/markdown'
  def format_out(self, inp, _env, writeable):
    inp.to_markdown(writeable, index=False)
    # to_markdown doesn't terminate last line:
    writeable.write('\n')
register(MarkdownOut, 'md', ['md-', 'markdown'],
         synopsis="Generate a Markdown table.",
         preferred_suffix='.md')

class JsonIn(FormatIn):
  def format_in(self, readable, _env):
    orient = self.opt('orient', 'records')
    return pd.read_json(readable, orient=orient)
register(JsonIn, '-json', [],
         synopsis="Parse JSON.",
         preferred_suffix='.json')

class JsonOut(FormatOut):
  def format_out(self, inp, _env, writeable):
    if isinstance(inp, pd.DataFrame):
      return inp.to_json(writeable, orient='records', date_format='iso', index=False, indent=2)
    else:
      return json.dump(inp, writeable, indent=2)
register(JsonOut, 'json-', ['json', 'js-'],
        synopsis="Generate JSON array of objects.",
        preferred_suffix='.tsv')
