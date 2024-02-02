import re
import tabulate
# from icecream import ic
import pandas as pd
from .command import section, command
from .formats import FormatOut, FormatIn

section('Format', 20)

@command
class MarkdownIn(FormatIn):
  '''
  markdown-in - Parse Markdown.
  aliases: -markdown, -md, md-in

# Convert TSV to Markdown to CSV:
$ psv in a.tsv // md- // out a.md
$ psv in a.md // -md // csv

  :suffixes: .md,.markdown
  '''
  def format_in(self, readable, _env):
    lines = readable.read().decode('utf-8')
    lines = lines.split('\n')
    want_header = self.opt('header', True)
    header = None
    records = []
    for line in lines:
      line = line.strip()
      if re.match(r'^\|[-:]-.*?-[-:]\|$', line):
        if not header and want_header:
          header = records.pop(0)
      elif line:
        line = re.sub(r'^\|\s*|\s*\|$', '', line)
        record = re.split(r'\s+\|\s+', line)
        records.append(record)
    if not header and records:
      header = [f'c{i}' for i in range(0, len(records[0]))]
    return pd.DataFrame(data=records, columns=header)


@command
class MarkdownOut(FormatOut):
  '''
  markdown-out - Generate Markdown.
  aliases: markdown-, markdown, md-out, md-, md

# Convert TSV on STDIN to Markdown:
$ cat a.tsv | psv -tsv // md

  :suffixes: .md,.markdown
  '''
  def format_out(self, inp, _env, writeable):
    tabulate.PRESERVE_WHITESPACE = True
    inp.to_markdown(writeable, index=False)
    # to_markdown doesn't terminate last line:
    writeable.write('\n')
