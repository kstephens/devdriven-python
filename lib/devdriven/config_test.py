import shlex
from devdriven.config import Config, MacroExpander
from icecream import ic

#############################

conf = Config(file_default='tests/devdriven/data/config.yml').load()
ic(conf)

macros = {
  'foo': 'bar 1: $1 1q: "$1" 2: $2 2q: "$2" @: $@ @q: "$@" rest'
}
mx = MacroExpander(macros=macros)

cmd = ['foo', 'a', 'b c']

ic(mx.expand_macro(cmd))
