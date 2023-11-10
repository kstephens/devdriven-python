import re
import os
import subprocess
import shlex
from devdriven.util import cwd
from .command import Command, command

@command('example', [],
          synopsis="Show examples.")
class Example(Command):
  def xform(self, _inp, _env):
    comments = []
    lines = self.examples()
    while lines:
      line = lines.pop(0).strip()
      if not line:
        None
      elif re.match(r'^#', line):
        comments.append(line)
      elif mtch := re.match(r'^\$ +(.*)$', line):
        print('\n'.join(comments))
        comments = []
        print(line)
        self.run_example(mtch.group(1))
        print('')

  def run_example(self, example):
    with cwd(f'{self.main.root_dir}/example'):
      if re.match(r'.+[|<>].+', example):
        self.run_command(example)
      elif re.match(r'^psv ', example):
        self.run_main(example)
      else:
        raise Exception(f"invalid example: {example!r}")

  def run_main(self, example):
    cmd_argv = shlex.split(example)
    instance = self.main.__class__()
    instance.prog_path = self.main.prog_path
    instance.run(cmd_argv)

  def run_command(self, cmd):
    env = os.environ
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

# -tsv: Convert content to tsv:
$ psv in a.tsv // -tsv // md
$ psv in https://tinyurl.com/4sscj338 // -tsv // md
$ cat a.tsv | psv -tsv // md

# csv: Convert tsv to csv:
$ psv in a.tsv // -tsv // csv-

# csv: Convert tsv to csv and save to a file:
$ psv in a.tsv // -tsv // csv- // out a.csv

# md: Convert tsv on stdin to Markdown:
$ cat a.tsv | psv -tsv // md

# json: Convert csv to json:
$ psv in a.csv // -csv // json-

# add-sequence (seq): add a column with a sequence:
$ psv in a.tsv // -tsv // seq // md

# add-sequence (seq): start at 0:
$ psv in a.tsv // -tsv // seq --start=0 // md

# add-sequence (seq): step by 2:
$ psv in a.tsv // -tsv // seq --step=2 // md

# add-sequence (seq): start at 5, step by -2:
$ psv in a.tsv // -tsv // seq --start=5 --step=-2 // md

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

# grep: match
$ psv in a.tsv // -tsv // grep d '.*x.*' // md

# grep: match d and b:
$ psv in a.tsv // -tsv // grep d '.*x.*' b '.*3$' // md

# sort: decreasing:
$ psv in a.tsv // -tsv // sort -r a // md

# sort by a decreasing, c increasing,
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

# stats: basic stats:
$ psv in a.tsv // -tsv // stats // md

# extract: extract fields by regex:
$ psv in users.txt // extract '^(?P<login>[^:]+)' // md
$ psv in users.txt // extract '^(?P<login>[^:]+):(?P<rest>.*)' // md
$ psv in users.txt // extract --unnamed '^(?P<login>[^:]+)(.*)' // md
$ psv in users.txt // extract --unnamed='group-%d' '^(?P<login>[^:]+)(.*)' // md

# null: does nothing:
$ psv in a.tsv // -tsv // null IGNORED --OPTION=VALUE // md

# env: display proccessing info:
$ psv in a.tsv // -tsv // show-columns // md // env-

'''.splitlines()
