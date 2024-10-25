from typing import Any, List, Dict
import os
import re
import logging
from devdriven import util

GIT_REPO_SSH_RX = re.compile(r'^(?P<user>[^@]+)@(?P<host>[^:]+):(?P<org>[^/]+)/(?P<repo>.+?)\.git$')
def git_repo_url(location: str) -> str:
  if m := re.match(GIT_REPO_SSH_RX, location):
    return f'https://{m.group("host")}/{m.group("org")}/{m.group("repo")}'
  return location

class GitDiff:
  def __init__(self, directory: str = '.'):
    self.directory: str = os.path.normpath(directory)

  def files_changed(self, ref1: str, ref2: str) -> List[str]:
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
  def __init__(self, directory: str, line: str):
    self.directory: str = directory
    self.ref, self.timestamp, self.committer_email, self.subject = line.split('\t', 4)

  def to_dict(self) -> Dict[str, Any]:
    return {
      'ref': self.ref,
      'timestamp': self.timestamp,
      'committer_email': self.committer_email,
      'directory': self.directory,
      'subject': self.subject
    }

class GitLog:
  def __init__(self, directory: str = '.'):
    self.directory: str = os.path.normpath(directory)
    self.commands: List[List[str]] = []

  def all(self) -> List[GitCommit]:
    return self.git_log([])

  def commits_between(self, ref1: str, ref2: str) -> List[GitCommit]:
    lines = self.run_git_log([f'{ref1:s}..{ref2:s}'])
    # ref2 may be an ancestor of ref1:
    lines += self.run_git_log([f'{ref2:s}..{ref1:s}'])
    # git log ref1..ref2 may not contain both ref1 and ref2:
    lines += self.run_git_log(['--max-count=1', ref1])
    lines += self.run_git_log(['--max-count=1', ref2])
    return self.parse_lines(list(set(lines)))

  def git_log(self, options: List[str]) -> List[GitCommit]:
    return self.parse_lines(self.run_git_log(options))

  def run_git_log(self, options: List[str]) -> List[str]:
    command = [
      'git', '-C', self.directory,
      'log',
      '--format=format:%H\t%aI\t%ce\t%s', *options,
      '--', '.',
    ]
    self.commands.append(command)
    result = util.exec_command(command, check=True, capture_output=True)
    return result.stdout.decode('utf-8').splitlines()

  def parse_lines(self, lines: List[str]) -> List[GitCommit]:
    logging.debug('lines %d', len(lines))
    return sorted([GitCommit(self.directory, line) for line in lines],
                  key=lambda g: g.timestamp)

class GitRevParse:
  def __init__(self, directory: str):
    self.directory = os.path.normpath(directory)

  def rev_parse(self, ref: str, *opts) -> List[str]:
    result = util.exec_command(
      [
        'git', '-C', self.directory,
        'rev-parse', '--verify',
        ref,
        *opts,
      ],
      check=True, capture_output=True)
    return sorted(result.stdout.decode('utf-8').splitlines())

def rev_parse(directory: str, ref: str, *opts) -> List[str]:
  return GitRevParse(directory).rev_parse(ref, *opts)
