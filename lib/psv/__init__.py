from icecream import ic, install
from . import command
from . import pipeline
from . import io
from . import formats
from . import yaml
from . import spreadsheet
from . import process
from . import summary
from . import metadata
from . import extract
from . import expr
from . import repl
# pylint: disable-next=redefined-builtin
from . import help
from . import example
install()
ic.configureOutput(includeContext=True)