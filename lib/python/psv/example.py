import re
import os
import subprocess
import shlex
from devdriven.util import cwd
from .command import Command, command

@command()
class Example(Command):
  '''
  examples - Show examples.

  Aliases: ex, example

  SEARCH-STRING : Matches name, aliases, synopsis

  --run, -r     : Run examples.
  '''
  def xform(self, _inp, _env):
    examples = self.parse_examples(self.examples())
    comment_rx = re.compile(f'(?i).*{"|".join(self.args)}.*')
    examples = [ex for ex in examples if re.match(comment_rx, ex[0])]
    self.run_examples(examples)

  def run_examples(self, examples):
    last_comment = None
    for comment, cmd in examples:
      if last_comment != comment:
        last_comment = comment
        print(comment)
      print('$ ' + cmd)
      if self.opt('run', self.opt('r', False)):
        self.run_example(cmd)
      print('')
      #if gen_docstring:
      #  print('\n====================\n\n')

  def parse_examples(self, lines):
    examples = []
    comments = []
    for line in lines:
      line = line.strip()
      if not line:
        comments = []
      elif re.match(r'^#', line):
        comments.append(line)
      elif mtch := re.match(r'^\$ +(.*)$', line):
        examples.append((
          '\n'.join(comments),
          mtch.group(1)
        ))
    return examples

  def run_example(self, example):
    with cwd(f'{self.main.root_dir}/example'):
      if re.match(r'.+ [|<>;] .+', example):
        self.run_command(example)
      elif re.match(r'^psv ', example):
        self.run_main(example)
      else:
        self.run_command(example)

  def run_main(self, cmd):
    # logging.warning('run_main: %s', repr(cmd))
    cmd_argv = shlex.split(cmd)
    instance = self.main.__class__()
    instance.prog_path = self.main.prog_path
    instance.run(cmd_argv)

  def run_command(self, cmd):
    # logging.warning('run_command: %s', repr(cmd))
    env = os.environ
    if env.get('PSV_RUNNING'):
      return
    env = env | {
      "PSV_RUNNING": '1',
      'PATH': f'{self.main.bin_dir}:{env["PATH"]}'
    }
    subprocess.run(cmd,
                   shell=True,
                   env=env)

  def examples(self):
    return '''
# in: read from STDIN:
$ cat a.tsv | psv in -
$ cat a.tsv | psv in

# in: HTTP support:
$ psv in https://tinyurl.com/4sscj338

# -tsv: Convert content to TSV:
$ psv in a.tsv // -tsv // md
$ psv in https://tinyurl.com/4sscj338 // -tsv // md
$ cat a.tsv | psv -tsv // md

# csv: Convert TSV to CSV:
$ psv in a.tsv // -tsv // csv-

# out: Convert TSV to CSV and save to a file:
$ psv in a.tsv // -tsv // csv- // out a.csv

# md: Convert TSV on stdin to Markdown:
$ cat a.tsv | psv -tsv // md

# json: Convert CSV to JSON:
$ psv in a.csv // -csv // json-

# -table: Parse generic table:
$ psv in users.txt // -table --fs=":"
$ psv in users.txt // -table --fs=":" --column='col%02d'
$ psv in us-states.txt // -table --header --fs="\s{2,}" // head 5 // md

# html: Generate HTML:
$ psv in users.txt // -table --header --fs=":" // html // o /tmp/users.html
$ w3m -dump /tmp/users.html

# cut: select columns by index and name:
$ psv in -i a.tsv // cut 2,d // md

# cut: remove c, put d before other columns,
$ psv in -i a.tsv // cut d '*' c:- // md

# range: select a range of rows:
$ psv in a.tsv // -tsv // seq --start=0 // range 1 3 // md

# range: every even row:
$ psv in a.tsv // -tsv // seq --start=0 // range --step=2 // md

# head:
$ psv in us-states.txt // -table // head 5 // md

# tail:
$ psv in us-states.txt // -table // tail 3 // md

# reverse (tac):
$ psv in a.tsv // -tsv // seq // tac // md

# grep: match columns by regex:
$ psv in a.tsv // -tsv // grep d '.*x.*' // md

# grep: match d and b:
$ psv in -i a.tsv // grep d '.*x.*' b '.*3$' // md

# sort: decreasing:
$ psv in a.tsv // -tsv // sort -r a // md

# sort: by a decreasing, c increasing,
# remove c, put d before other columns,
# create a column i with a seqence
$ psv in a.tsv // -tsv // sort a:- c // cut d '*' c:- // seq i 10 5 // md


# translate: change delete characters:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // tr -d ', ' // head // md
$ psv in us-states.txt // -table --header --fs="\s{2,}" // tr ',' '_' Population // head // md

# rename: rename column 'b' to 'B':
$ psv in a.tsv // -tsv // rename b B // md

# show-columns: show column metadata:
$ psv in a.tsv // -tsv // show-columns // md

# add-sequence (seq): add a column with a sequence:
$ psv in a.tsv // -tsv // seq // md

# add-sequence (seq): start at 0:
$ psv in a.tsv // -tsv // seq --start=0 // md

# add-sequence (seq): step by 2:
$ psv in a.tsv // -tsv // seq --step=2 // md

# add-sequence (seq): start at 5, step by -2:
$ psv in a.tsv // -tsv // seq --start=5 --step=-2 // md

# extract: extract fields by regex:
$ psv in users.txt // extract '^(?P<login>[^:]+)' // md
$ psv in users.txt // extract '^(?P<login>[^:]+):(?P<rest>.*)' // md
$ psv in users.txt // extract --unnamed '^(?P<login>[^:]+)(.*)' // md
$ psv in users.txt // extract --unnamed='group-%d' '^(?P<login>[^:]+)(.*)' // md

# stats: basic stats:
$ psv in a.tsv // -tsv // stats // md

# html: generate html
$ psv in us-states.txt // -table --header --fs="\s{2,}" // head // html // o /tmp/us-states.html
$ w3m -dump /tmp/us-states.html

# null: does nothing:
$ psv in a.tsv // -tsv // null IGNORED --OPTION=VALUE // md

# env: display proccessing info:
$ psv in a.tsv // -tsv // show-columns // md // env-

'''.splitlines()
