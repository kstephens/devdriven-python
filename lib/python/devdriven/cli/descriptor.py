import re
from dataclasses import dataclass
from typing import List
from devdriven.cli.options import Options
from devdriven.util import set_from_match, dataclass_from_dict, dataclass_from_dict, unpad_lines
from icecream import ic

_sections = []
def sections():
  return _sections
current_section = 'UNKNOWN'
def begin_section(name):
  global current_section
  assert name
  current_section = name
  if name not in _sections:
    _sections.append(name)

@dataclass
class Descriptor():
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

  def parse_docstring(self, docstr):
    found_aliases = None
    debug = False
    lines = unpad_lines(docstr.splitlines())
    comments = []
    while lines:
      line = lines.pop(0)
      if debug:
        ic(line)
      m = None
      if m := re.match(r'^:(?P<name>[a-z_]+)[:=] *(?P<value>.*)', line):
        setattr(self, m.group('name'), m.group('value').strip())
      elif m := not self.name and re.match(r'^(?P<name>[-a-z]+) +- +(?P<brief>.+)', line):
        set_from_match(self, m)
      elif m := not found_aliases and re.match(r'(?i)^Alias(?:es)?: +(.+)', line):
        self.aliases.extend(re.split(r'\s*,\s*|\s+', m[1].strip()))
        found_aliases = True
      elif m := re.match(r'(?i)^(Arguments|Options|Examples):\s*$', line):
        None
      elif m := re.match(r'^[#] (.+)', line):
        comments.append(m[1])
      elif m := re.match(r'^\$ (.+)', line):
        self.examples.append(Example(command=m[1], comments=comments))
        comments = []
      elif m := self.options.parse_docstring(line):
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

  def preferred_suffix(self):
    return self.suffix_list and self.suffix_list[0]

  def x_opt_by_name(self, name, aliases=False):
    return self.options.opt_by_name(name, aliases)

  def get_opt_aliases(self, opt):
    return self.options.get_opt_aliases(opt)

  def build_synopsis(self):
    cmd = ['psv', self.name] + self.options.command_synopsis()
    self.synopsis = ' '.join(cmd)

  def trim_detail(self):
    while self.detail and not self.detail[0]:
      self.detail.pop(0)
    while self.detail and not self.detail[-1]:
      self.detail.pop(-1)

@dataclass
class Example():
  command: str
  comments: List[str]

DEFAULTS = {
  'section': '',
  'content_type': None,
  'content_encoding': None,
  'suffixies': '',
}

def create_descriptor(klass):
  assert current_section
  options = Options()
  kwargs = {
    'name': '',
    'brief': '',
    'synopsis': '',
    'aliases': [],
    'detail': [],
    'examples': [],
    'suffixes': '',
    'suffix_list': [],
  } | DEFAULTS | {
    'section': current_section,
    'klass': klass,
    'options': options,
  }
  return dataclass_from_dict(Descriptor, kwargs).parse_docstring(klass.__doc__)
