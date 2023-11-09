import re

def select_columns(inp, args, check=False):
  inp_cols = list(inp.columns)
  selected = []
  for col in args:
    action = '+'
    if mtch := re.match(r'^([^:]+):([-+]?)$', col):
      col = mtch.group(1)
      action = mtch.group(2)
    if col == '*':
      cols = inp_cols
    else:
      cols = [col]
    if action == '-':
      selected = [x for x in selected if x not in cols]
    else:
      selected = selected + [x for x in cols if x not in selected]
  if check:
    if unknown := [col for col in selected if col not in inp_cols]:
      raise Exception(f"unknown columns: {unknown!r} : available {inp_cols!r}")
  return selected
