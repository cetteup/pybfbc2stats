from typing import Dict, Union, Optional, List

from .constants import ENCODING

StrValue = Union[str, bytes]
IntValue = Union[int, str, bytes]
FloatValue = Union[float, str, bytes]
PayloadValue = Optional[Union[StrValue, IntValue, FloatValue]]


class Payload:
    data: Dict[str, bytes]

    def __init__(self, **kwargs: PayloadValue):
        self.data = dict()
        self.update(**kwargs)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Payload':
        self = cls()
        for line in data.split(b'\n'):
            key, _, value = line.partition(b'=')
            self.set(key.decode(ENCODING), value)

        return self

    def __bytes__(self):
        lines = []
        for key, value in self.data.items():
            lines.append(key.encode(ENCODING) + b'=' + value)

        return b'\n'.join(lines)

    def __len__(self):
        return len(bytes(self))

    def update(self, **kwargs: PayloadValue) -> None:
        for key, value in kwargs.items():
            self.set(key, value)

    def set(self, key: str, value: PayloadValue) -> None:
        if isinstance(value, bytes):
            self.data[key] = value
            return

        if value is None:
            self.data[key] = b''
            return

        self.data[key] = str(value).encode(ENCODING)

    def get(self, key: str, default: Optional[bytes] = None) -> Optional[bytes]:
        return self.data.get(key, default)

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value = self.get(key)
        if value is None:
            return default

        return value.decode(ENCODING)

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        value = self.get(key)
        if value is None:
            return default

        return int(value.decode(ENCODING))

    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        value = self.get(key)
        if value is None:
            return default

        return float(value.decode(ENCODING))


class FeslPayload(Payload):
    # TODO Make more generic, just handle any passed data format
    def set_list(self, items: List[Union[PayloadValue, Dict[str, PayloadValue]]], prefix: str) -> None:
        # TODO This comment is outdated, format is different for non-dict values
        # Convert item list following "prefix.index.key=value"-format
        for index, item in enumerate(items):
            if isinstance(item, dict):
                for key, value in item.items():
                    dotted_elements = [prefix, index, key]
                    # dict with prefix: userInfo.0.userName=NoobKillah
                    self.set(self.build_list_key(dotted_elements), value)
            else:
                dotted_elements = [prefix, index]
                # list with prefix only: keys.0=accuracy
                self.set(self.build_list_key(dotted_elements), item)

        # Add list length indicator
        self.set(f'{prefix}.[]', len(items))

    @staticmethod
    def build_list_key(dotted_elements: List[Union[str, int]]) -> str:
        return '.'.join(map(str, dotted_elements))
