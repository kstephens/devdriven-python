from typing import Any, Optional, Union, List, Sequence, Self
from pathlib import Path
from dataclasses import dataclass, field
import importlib.util

Pathish = Union[Path, str]
PathishMaybe = Optional[Pathish]
Paths = Sequence[Pathish]

@dataclass
class Resources:
  search_paths: List[str] = field(default_factory=list)

  def rel_path(self, path: Pathish) -> Path:
    assert self.search_paths
    return Path(self.search_paths[0]).joinpath(path)

  def read(self, names: Paths, default=None, encoding=None) -> Any:
    file = self.find(names, None)
    if file is None:
      if default is not None:
        return default
      raise Exception(f'cannot locate resource {names!r} in {self.search_paths!r}')
    with open(file, 'r', encoding=encoding) as file:
      return file.read()

  def find(self, names: Paths, default=None) -> Any:
    if paths := self.find_all(names):
      return paths[0]
    return default

  def find_all(self, names: Paths) -> Sequence[Path]:
    def path_names(path):
      path = Path(path)
      path_names = [path.joinpath(name) for name in names if name]
      return [str(p) for p in path_names if p.is_file()]
    return sum(map(path_names, self.search_paths), [])

  def module_path(self, module_name: str) -> Path:
    if spec := importlib.util.find_spec(module_name, None):
      if spec.origin:
        return Path(spec.origin)
    raise Exception(f'module_path : {module_name!r}')

  def module_dir(self, module_name: str) -> Path:
    if origin := self.module_path(module_name):
      return origin.parent
    raise Exception(f'module_dir : {module_name!r}')

  def add_module_dir(self, module_name: str, rel: PathishMaybe = None) -> Self:
    return self.append_search_path(self.module_dir(module_name), rel)

  def add_file_dir(self, file: Pathish, rel: PathishMaybe = None) -> Self:
    return self.append_search_path(Path(file).parent, rel)

  def append_search_path(self, path: Pathish, rel: PathishMaybe = None) -> Self:
    path = Path(path)
    if rel:
      path = path / rel
    self.search_paths.append(str(path))
    return self
