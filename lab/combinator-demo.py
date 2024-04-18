#!/usr/bin/env python3.11
from devdriven.showing_is_seeing import ShowingIsSeeing
with open('lab/combinator-examples.py') as input:
  demo_exprs = input.read()
ShowingIsSeeing(lambda : globals()).eval_exprs(demo_exprs)
