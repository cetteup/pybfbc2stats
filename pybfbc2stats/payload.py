from typing import Dict, Union, Optional, List

from .constants import ENCODING
from .exceptions import ParameterError

StrValue = Union[str, bytes]
IntValue = Union[int, str, bytes]
FloatValue = Union[float, str, bytes]
PayloadValue = Optional[Union[StrValue, IntValue, FloatValue]]
PayloadStruct = Optional[Union[Dict[str, Union[PayloadValue, 'PayloadStruct']], List[Union[PayloadValue, 'PayloadStruct']]]]


class Payload:
    data: Dict[str, bytes]
    is_list: bool

    def __init__(self, *args: Union[PayloadValue, PayloadStruct], **kwargs: Union[PayloadValue, PayloadStruct]):
        self.data = dict()
        if len(args) > 0:
            self.is_list = True
            self.extend(*args)
        else:
            self.is_list = False
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

    def update(self, **kwargs: Union[PayloadValue, PayloadStruct]) -> None:
        if self.is_list:
            raise ParameterError('Cannot set key values on list payload')

        for key, value in kwargs.items():
            self.set(key, value)

    def extend(self, *args) -> None:
        if not self.is_list:
            raise ParameterError('Cannot set index values on non-list payload')

        length = len(self.data)
        for index, value in enumerate(args):
            self.set(str(length + index), value)

    def set(self, key: str, value: Union[PayloadValue, PayloadStruct], *args: Union[str, int]) -> None:
        path = self.build_path(*args, key)
        if isinstance(value, dict):
            # TODO Would not overwrite old keys under path if existing sub_key is not in value
            for sub_key, sub_value in value.items():
                self.set(sub_key, sub_value, *args, key)
            return

        if isinstance(value, list):
            for index, sub_value in enumerate(value):
                self.set(str(index), sub_value, *args, key)
            self.set(self.build_list_length_path(key), len(value), *args)
            return

        if isinstance(value, bytes):
            self.data[path] = value
            return

        if value is None:
            self.data[path] = b''
            return

        # TODO Quote values
        self.data[path] = str(value).encode(ENCODING)

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

    @staticmethod
    def build_path(*args: Union[str, int]) -> str:
        return '.'.join(map(str, args))

    @staticmethod
    def build_list_length_path(path: str) -> str:
        return Payload.build_path(path, '[]')
