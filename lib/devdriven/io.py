from typing import Any, Optional, Union, Self, List, IO
from dataclasses import dataclass, field
from io import StringIO

Data = Union[str, bytes]


@dataclass
class BroadcastIO:
    streams: List[IO] = field(default_factory=list)

    def print(self, data: Data, *args, **kwargs) -> None:
        for stream in self.streams:
            kwargs["file"] = stream
            print(self._coerce_data(data, stream), *args, **kwargs)

    def write(self, data: Data, *args, **kwargs) -> None:
        for stream in self.streams:
            stream.write(self._coerce_data(data, stream), *args, **kwargs)

    def _coerce_data(self, data: Data, stream: IO) -> Data:
        if isinstance(data, bytes) and isinstance(stream, StringIO):
            return data.decode("utf-8")
        return data

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()

    def close(self) -> None:
        return None

    def push(self, stream: Optional[IO] = None) -> Self:
        if not stream:
            stream = StringIO()
        self.streams.append(stream)
        return self

    def pop(self) -> Any:
        return self.streams.pop(-1)
