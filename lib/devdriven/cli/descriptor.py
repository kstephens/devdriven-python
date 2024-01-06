from __future__ import annotations
from typing import Optional, List
import re
from dataclasses import dataclass
from devdriven.cli.options import Options
from devdriven.util import set_from_match, unpad_lines
from icecream import ic

@dataclass
class Descriptor:
  klass: object
  name: str
  brief: str
  synopsis: str
  aliases: list
  detail: list
  options: Options
  examples: list
  section: str
  content_type: str      # = None
  content_encoding: str  # = None
  suffixes: str          # ".csv,.txt,...""
  suffix_list: list
  data: object

  def parse_docstring(self, docstr: str) -> Descriptor:
    found_aliases = False
    debug = False
    lines = unpad_lines(re.sub(r'\\\n', '', docstr).splitlines())
    comments = []
    while lines:
      line = lines.pop(0)
      if debug:
        ic(line)
      m = None
      if m := re.match(r'^:(?P<name>[a-z_]+)[:=] *(?P<value>.*)', line):
        setattr(self, m.group('name'), m.group('value').strip())
      elif m := re.match(r'^(?P<name>[-a-z]+) +- +(?P<brief>.+)', line) if not self.name else None:
        set_from_match(self, m)
      elif m := re.match(r'(?i)^Alias(?:es)?: +(.+)', line) if not found_aliases else None:
        self.aliases.extend(re.split(r'\s*,\s*|\s+', m[1].strip()))
        found_aliases = True
      elif m := re.match(r'(?i)^(Arguments|Options|Examples):\s*$', line):
        # pylint: disable-next=pointless-statement
        None
      elif m := re.match(r'^[#] (.+)', line):
        comments.append(m[1])
      elif m := re.match(r'^\$ (.+)', line):
        self.examples.append(Example(command=m[1], comments=comments))
        comments = []
      elif self.options.parse_docstring(line):
        if debug:
          ic((self.name, self.options))
      else:
        self.detail.append(line)
      if debug:
        ic(m and m.groupdict())
    if self.suffixes:
      self.suffix_list = [x.strip() for x in re.split(r'\s*,\s*', self.suffixes)]
    self.build_synopsis()
    self.trim_detail()
    return self

  def preferred_suffix(self) -> Optional[str]:
    return self.suffix_list[0] if self.suffix_list else None

  def get_opt_aliases(self, opt):
    return self.options.get_opt_aliases(opt)

  def build_synopsis(self) -> None:
    cmd = ['psv', self.name] + self.options.command_synopsis()
    self.synopsis = ' '.join(cmd)

  def trim_detail(self) -> None:
    while self.detail and not self.detail[0]:
      self.detail.pop(0)
    while self.detail and not self.detail[-1]:
      self.detail.pop(-1)

@dataclass
class Example:
  command: str
  comments: List[str]
