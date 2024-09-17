import re

GLOB_RX = re.compile(r'(?P<dot>\.)|(?P<char>\?)|(?P<star_star>\*\*)|(?P<begin_star>(?P<pre_star>^|/)\*)|(?P<star>\*)')

def glob_to_regex(glob: str) -> str:
  def scan(m):
    if m['dot']:
      return r'\.'
    if m['char']:
      return r'[^/.]'
    if m['star_star']:
      return r'(?![./]).+'
    if m['begin_star']:
      return m['pre_star'] + r'(?![./])[^/]*'
    if m['star']:
      return r'(?:[^/]*)'
    assert not 'here'
    return None
  return re.compile('^(?:' + re.sub(GLOB_RX, scan, glob) + ')$')
  # ic((glob, rx))
  # return rx
