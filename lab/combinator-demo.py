#!/usr/bin/env python3.11
import sys
from devdriven.showing_is_seeing import ShowingIsSeeing, ConvertJupyterToCode

if False:
  code = ConvertJupyterToCode(
  ).read(
    'lab/combinator_examples.ipynb'
  ).parse(
  ).extract(
  ).as_string()
  print(code)
  sys.exit(0)

with open('lab/combinator_examples.py') as input:
  demo_exprs = input.read()
ShowingIsSeeing(lambda : globals()).setup_logging().eval_exprs(demo_exprs)

