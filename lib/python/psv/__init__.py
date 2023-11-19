from icecream import ic, install
from . import command
from . import pipeline
from . import io
from . import formats
from . import process
from . import summary
from . import metadata
from . import extract
from . import expr
from . import repl
from . import help
from . import example
install()
ic.configureOutput(includeContext=True)
