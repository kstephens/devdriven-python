#!/usr/bin/env python3.10
print(__file__); print(__name__)
import sys
import psv.main
# from tsv import Main
# import tsv


sys.exit(psv.main.Main().run(sys.argv).exit_code)
