from . import base
import re
import os
import sys
import subprocess
from devdriven.util import cwd
import shlex

class Example(base.Base):
  def xform(self, _inp):
    comments = []
    lines = self.examples()
    while lines:
      line = lines.pop(0).strip()
      if re.match(r'^#', line):
        comments.append(line)
      elif mtch := re.match(r'^\$ +(.*)$', line):
        print('\n'.join(comments))
        comments = []
        print(line)
        self.run_example(mtch.group(1))
        print('')

  def run_example(self, example):
    with cwd(f'{self.main.root_dir}/tmp'):
      if re.match(r'\|<|>', example):
        self.run_command(example)
      elif re.match(r'^psv ', example):
        self.run_main(example)

  def run_main(self, example):
        cmd_argv = shlex.split(example)
        instance = self.main.__class__()
        instance.prog_path = self.main.prog_path
        instance.run(cmd_argv)

  def run_command(self, command):
      env = os.environ
      env = env | {
        "PSV_RUNNING": '1',
        'PATH': f'{self.main.bin_dir}:{env["PATH"]}'
      }
      print('$ '+ command)
      result = subprocess.run(command,
                              shell=True,
                              # capture_output=True,
                              env=env)

  def examples(self):
    return '''
# csv: Convert tsv to csv:
$ psv in a.tsv // -tsv // csv-

# md: Convert tsv on stdin to Markdown:
$ cat a.tsv | psv -tsv // md

# add-seqence (seq): add a column with a sequence:
$ psv in a.tsv // -tsv // seq // md

# add-seqence (seq): start at 0:
$ psv in a.tsv // -tsv // seq --start 0 // md

# add-seqence (seq): step by 2:
$ psv in a.tsv // -tsv // seq --step 2 // md

# add-seqence (seq): start at 5, step by -2:
$ psv in a.tsv // -tsv // seq --start 5 --step -2 // md

# range: select a range of rows:
$ psv in a.tsv // -tsv // seq --start 0 // range 1 3 // md

# range: every even row:
psv in a.tsv // -tsv // seq --start 0 // range --step 2 // md

# reverse (tac):
$ psv in a.tsv // -tsv // seq // tac // md

# grep:
$ psv in a.tsv // -tsv // grep d '.*x.*' b '.*3$' // md

# sort by a decreasing, c increasing,
# remove c, put d before other columns,
# create a column i with a seqence
$ psv in a.tsv // -tsv // sort a:- c // cut 'd' '*' c:- // seq i 10 5 // md

# rename: rename column 'b' to 'B'
$ psv in a.tsv // -tsv // rename b B // md

# null: does nothing:
$ psv in a.tsv // -tsv // null IGNORED --OPTION=VALUE // md

'''.splitlines()

base.register(Example, 'example', [],
              synopsis="Show examples.")
