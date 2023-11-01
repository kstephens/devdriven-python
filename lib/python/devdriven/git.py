import os
import logging
from devdriven import util

class GitDiff:
  def __init__(self, directory='.'):
    self.directory = os.path.normpath(directory)

  def files_changed(self, ref1, ref2):
    result = util.exec_command(
      [
        'git', '-C', self.directory,
        'diff',
        '--name-only', ref1, ref2,
        '--', '.',
      ],
      check=True, capture_output=True)
    return sorted(result.stdout.decode('utf-8').splitlines())

class GitCommit:
  def __init__(self, directory, line):
    self.directory = directory
    self.ref, self.timestamp, self.committer_email, self.subject = line.split('\t', 4)

  def to_dict(self):
    return {
      'ref': self.ref,
      'timestamp': self.timestamp,
      'committer_email': self.committer_email,
      'directory': self.directory,
      'subject': self.subject
    }

class GitLog:
  def __init__(self, directory='.'):
    self.directory = os.path.normpath(directory)
    self.commands = []

  def all(self):
    return self.git_log([])

  def commits_between(self, ref1, ref2):
    lines = self.run_git_log([f'{ref1:s}..{ref2:s}'])
    # ref2 may be an ancestor of ref1:
    lines += self.run_git_log([f'{ref2:s}..{ref1:s}'])
    # git log ref1..ref2 may not contain both ref1 and ref2:
    lines += self.run_git_log(['--max-count=1', ref1])
    lines += self.run_git_log(['--max-count=1', ref2])
    return self.parse_lines(list(set(lines)))

  def git_log(self, options):
    return self.parse_lines(self.run_git_log(options))

  def run_git_log(self, options):
    command = [
      'git', '-C', self.directory,
      'log',
      '--format=format:%H\t%aI\t%ce\t%s', *options,
      '--', '.',
    ]
    self.commands.append(command)
    return util.exec_command(command, check=True, capture_output=True) \
      .stdout.decode('utf-8').splitlines()

  def parse_lines(self, lines):
    logging.debug('lines %d', len(lines))
    return sorted([GitCommit(self.directory, line) for line in lines],
                  key=lambda g: g.timestamp)

class GitRevParse:
  def __init__(self, directory='.'):
    self.directory = os.path.normpath(directory)

  def rev_parse(self, ref, *opts):
    result = util.exec_command(
      [
        'git', '-C', self.directory,
        'rev-parse', '--verify',
        ref,
        *opts,
      ],
      check=True, capture_output=True)
    return sorted(result.stdout.decode('utf-8').splitlines())

def rev_parse(dir, ref, *opts):
    return GitRevParse(dir).rev_parse(ref, *opts)
