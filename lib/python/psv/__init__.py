# print(__file__); print(__name__)
# from . import main
from icecream import ic, install
install()
ic.configureOutput(includeContext=True)
