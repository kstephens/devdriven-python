from typing import Any, Optional, Self, List, IO
from dataclasses import dataclass, field
from io import StringIO

@dataclass
class BroadcastIO():
  streams: List[IO] = field(default_factory=list)

  def print(self, data, *args, **kwargs):
    for stream in self.streams:
      kwargs['file'] = stream
      print(self._coerce_data(data, stream), *args, **kwargs)

  def write(self, data, *args, **kwargs):
    for stream in self.streams:
      stream.write(self._coerce_data(data, stream), *args, **kwargs)

  def _coerce_data(self, data, stream):
    if isinstance(data, bytes) and isinstance(stream, StringIO):
      return data.decode('utf-8')
    return data

  def flush(self):
    for stream in self.streams:
      stream.flush()

  def close(self):
    return None

  def push(self, stream: Optional[Any] = None) -> Self:
    if not stream:
      stream = StringIO()
    self.streams.append(stream)
    return self

  def pop(self) -> Any:
    return self.streams.pop(-1)
