from icecream import ic, install
from . import command
from . import pipeline
from . import io
from . import formats
from . import process
from . import metadata
from . import extract
from . import expr
from . import repl
from . import example
from . import help
install()
ic.configureOutput(includeContext=True)
