from pathlib import Path
from typing import List
from dataclasses import dataclass

@dataclass
class Resources:
  search_paths: List[str]

  def read(self, names: List[str], default=None):
    file = self.find(names, None)
    if file is None:
      if default is not None:
        return default
      raise Exception(f'cannot locate resource {names!r} in {self.search_paths!r}')
    # pylint: disable-next=unspecified-encoding
    with open(file, 'r') as file:
      return file.read()

  def find(self, names: List[str], default=None):
    if paths := self.find_all(names):
      return paths[0]
    return default

  def find_all(self, names: List[str]) -> List[str]:
    def path_names(path):
      path = Path(path)
      path_names = [path.joinpath(name) for name in names if name]
      return [str(p) for p in path_names if p.is_file()]
    return sum(map(path_names, self.search_paths), [])
