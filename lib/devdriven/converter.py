from typing import Any, Optional, Union, Iterable, Callable, Type
from dataclasses import dataclass, field
import json
import yaml  # type: ignore
import pandas as pd  # type: ignore
from devdriven.util import splitkeep  # type: ignore

JSON = "json"
YAML = "yaml"
TYPE = type(int)


def identity(data: Any) -> Any:
    return data


@dataclass
class Converter:
    encoding: str = field(default="utf-8")
    record_separator: str = field(default="\n")
    rich_format: str = field(default=JSON)
    preprocess_func: Optional[Callable] = field(default=identity)

    def cannot_convert(self, msg: str, data: Any):
        raise TypeError(f"{msg}: cannot convert {type(data).__name__!r}")

    def as_type(self, data: Any, typ: Union[str, Type, None], *args):
        if typ is None:
            return data
        if isinstance(typ, TYPE):
            typ = typ.__name__
        fun: Optional[Callable] = getattr(self, f"as_{typ}", None)
        if fun is not None:
            return fun(data, *args)
        self.cannot_convert("as_type: {typ!r}", data)
        return None

    def as_bytes(self, data: Any) -> bytes:
        if isinstance(data, bytes):
            return data
        return self.as_str(data).encode(self.encoding)

    def as_str(self, data: Any) -> str:
        if isinstance(data, str):
            return data
        if isinstance(data, bytes):
            return data.decode(self.encoding)
        if isinstance(data, (int, float)):
            return str(data)
        if isinstance(data, pd.DataFrame):
            return str(data) + "\n"
        return str(self.as_rich(self.preprocess(data)))

    def as_int(self, data: Any) -> int:
        return int(data)

    def as_float(self, data: Any) -> float:
        return float(data)

    def as_rich(self, data: Any) -> Any:
        if self.rich_format == JSON:
            return json.dumps(self.preprocess(data), indent=2)
        if self.rich_format == YAML:
            return yaml.dump(self.preprocess(data), allow_unicode=True)
        self.cannot_convert("as_rich", data)
        return None

    def as_iterable(self, data: Any, elem_type: Optional[str] = None) -> Iterable:
        if isinstance(data, str):
            if elem_type == "str":
                return splitkeep(data, self.record_separator)
            if elem_type == "bytes":
                data = data.encode(self.encoding)
                return splitkeep(data, self.record_separator.encode(self.encoding))
            return self.as_iterable(self.as_str(data), "str")
        if isinstance(data, bytes):
            if elem_type == "bytes":
                return splitkeep(data, self.record_separator.encode(self.encoding))
            if elem_type == "str":
                return self.as_iterable(self.as_str(data), elem_type)
            return [self.as_type(data, elem_type)]
        if isinstance(data, list):
            if elem_type is None:
                return data
            return [self.as_type(elem, elem_type) for elem in data]
        if isinstance(data, tuple):
            if elem_type is None:
                return list(data)
            return [self.as_type(elem, elem_type) for elem in data]
        if isinstance(data, dict):
            if elem_type is None:
                return [list(kv) for kv in data.items()]
            return [self.as_type(elem, elem_type) for elem in data.items()]
        if isinstance(data, pd.DataFrame):
            if elem_type is None:
                # !!!: convert each DataFrame row into a str:
                return self.as_iterable(str(data) + "\n", elem_type)
            return self.as_iterable(str(data) + "\n", elem_type)
        return [self.as_type(data, elem_type)]

    def as_dict(
        self, data: Any, key_type: Optional[str] = None, val_type: Optional[str] = None
    ) -> dict:
        if isinstance(data, dict):
            if key_type is None and val_type is None:
                return data
            return {
                self.as_type(k, key_type): self.as_type(v, val_type)
                for k, v in data.items()
            }
        if isinstance(data, list):
            return self.as_dict(dict(data), key_type, val_type)
        if isinstance(data, tuple):
            return self.as_dict(list(data), key_type, val_type)
        if isinstance(data, pd.DataFrame):
            return {r[0]: r[1] for _i, r in data.iterrows()}
        self.cannot_convert("as_dict", data)
        return {}

    # pylint: disable-next=invalid-name
    def as_DataFrame(self, data: Any) -> Optional[pd.DataFrame]:
        if isinstance(data, pd.DataFrame):
            return data
        if isinstance(data, str):
            return pd.DataFrame(self.as_iterable(data, "str"))
        if isinstance(data, list):
            return self.as_DataFrame(self.as_iterable(data, None))
        if isinstance(data, dict):
            return pd.DataFrame(data=data.items(), columns=["key", "value"])
        if isinstance(data, Iterable):
            return pd.DataFrame([[elem] for elem in data])
        self.cannot_convert("as_DataFrame", data)
        return None

    def preprocess(self, data: Any) -> Any:
        if self.preprocess_func is None:
            return data
        return self.preprocess_func(data)
