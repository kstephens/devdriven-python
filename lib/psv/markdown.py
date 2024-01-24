import tabulate
# from icecream import ic
from .command import section, command
from .formats import FormatOut

section('Format', 20)

@command
class MarkdownOut(FormatOut):
  '''
  markdown - Generate Markdown.
  aliases: md, md-, markdown-

# md: Convert TSV on STDIN to Markdown:
$ cat a.tsv | psv -tsv // md

  :suffixes: .md,.markdown
  '''
  def format_out(self, inp, _env, writeable):
    tabulate.PRESERVE_WHITESPACE = True
    inp.to_markdown(writeable, index=False)
    # to_markdown doesn't terminate last line:
    writeable.write('\n')
