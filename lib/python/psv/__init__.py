# print(__file__); print(__name__)
# from . import main
from icecream import ic, install
install()
ic.configureOutput(includeContext=True)
from . import command, pipeline, io, format, process, metadata, repl, example, help
