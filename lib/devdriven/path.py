import re

def clean_path(path: str) -> str:
  prev = None
  while path != prev:
    prev = path
    path = re.sub(r'//+', '/', path)
    path = re.sub(r'^\./', '', path)
    path = re.sub(r'^\.\.(?:$|/)', '', path, 1)
    path = re.sub(r'(:?^/)\./', '/', path)
    path = re.sub(r'^/\.\.(?:$|/)', '/', path, 1)
    path = re.sub(r'^[^/]+/\.\.(?:$|/)', '', path, 1)
    path = re.sub(r'/[^/]+/\.\./', '/', path, 1)
  return path
