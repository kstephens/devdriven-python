#!/usr/bin/env python3.11
from devdriven.showing_is_seeing import ShowingIsSeeing
with open('lab/combinator_examples.py') as input:
  demo_exprs = input.read()
ShowingIsSeeing(lambda : globals()).setup_logging().eval_exprs(demo_exprs)
