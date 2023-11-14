import re
from dataclasses import dataclass
from typing import List
from devdriven.util import set_from_match, dataclass_from_dict, dataclass_from_dict, unpad_lines
from icecream import ic

@dataclass
class Descriptor():
  klass: object
  name: str
  brief: str
  synopsis: str
  aliases: list
  detail: list
  args: dict
  opts: dict
  opt_aliases: dict
  examples: list
  section: str
  content_type: str      # = None
  content_encoding: str  # = None
  preferred_suffix: str  # = None
  data: object

  def parse_docstring(self, docstr):
    found_aliases = None
    debug = False
    lines = unpad_lines(docstr.splitlines())
    def eat_blanks():
      while lines and not lines[0]:
        lines.pop(0)
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
      elif m := re.match(r'^(--?[^\|]+)[\|] *(.*)', line):
        name, *opt_aliases = map(lambda x: x.strip(), re.split(r', *', m[1].strip()))
        if debug:
          ic((name, opt_aliases))
        self.opts[name] = m[2].strip()
        for opt_alias in opt_aliases:
          self.opt_aliases[opt_alias] = name
      elif m := re.match(r'^([^\|]+)[\|] *(.*)', line):
        self.args[m[1].strip()] = m[2].strip()
      elif line:
        self.detail.append(line)
      if debug:
        ic(m and m.groupdict())
    cmd = [' ', 'psv', self.name, *self.opts.keys(), *self.args.keys()]
    self.synopsis = ' '.join(cmd)
    return self

@dataclass
class Example():
  command: str
  comments: List[str]

DEFAULTS = {
  'section': '',
  'content_type': None,
  'content_encoding': None,
  'preferred_suffix': '',
}

def create_descriptor(klass):
  kwargs = {
    'name': '',
    'brief': '',
    'synopsis': '',
    'aliases': [],
    'detail': [],
    'args': {},
    'opts': {},
    'opt_aliases': {},
    'examples': [],
  } | DEFAULTS | {
    "klass": klass,
  }
  return dataclass_from_dict(Descriptor, kwargs).parse_docstring(klass.__doc__)
