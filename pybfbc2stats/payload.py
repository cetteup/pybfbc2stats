from enum import Enum
from typing import Dict, Union, Optional, List, Callable, Type
from urllib.parse import unquote

from .constants import ENCODING, MagicParseKey
from .exceptions import Error, ParameterError

StrValue = Union[str, bytes]
IntValue = Union[int, str, bytes]
FloatValue = Union[float, str, bytes]
BoolValue = Union[bool, str, bytes]
PayloadValue = Optional[Union[StrValue, IntValue, FloatValue, BoolValue]]
PayloadStruct = Optional[Union[Dict[str, Union[PayloadValue, 'PayloadStruct']], List[Union[PayloadValue, 'PayloadStruct']]]]
ParseMap = Dict[str, Union[Type[str], Type[int], Type[float], Type[bool]]]
ParsedPayloadStruct = Dict[str, Union[PayloadValue, List[Union[PayloadValue, 'ParsedPayloadStruct']], 'ParsedPayloadStruct']]


class StructType(int, Enum):
    struct = 1
    list = 2
    map = 3


class StructLengthIndicator(str, Enum):
    list = '[]'
    map = '{}'

    def __str__(self):
        return self.value


class Payload:
    data: PayloadStruct

    def __init__(self, **kwargs: Union[PayloadValue, PayloadStruct]):
        self.data = dict()
        self.update(**kwargs)

    @classmethod
    def from_bytes(cls, data: bytes, parse_map: Optional[ParseMap] = None) -> 'Payload':
        self = cls()
        # Adapted from https://stackoverflow.com/a/2017083
        struct = dict()
        for line in data.split(b'\n'):
            path, _, value = line.partition(b'=')
            keys = Payload.destruct_path(path.decode(ENCODING))
            # Init target reference to base-level struct
            target = struct
            # Iterate over path elements, leaving out the last one since it will become the key in the lowest-level dict
            for key in keys[:-1]:
                """
                This nifty statement does either of the following:
                a) if the current-level dict does contain (a dict) at key,
                   it will update the target reference to that existing dict
                   => we go down one level in the tree to an existing dict
                b) if the current-level dict does *not* (a dict) at key,
                   it will create an empty dict at key and update the target reference to that new dict
                   => we create a new, lower level and go down one level to the new dict
                """
                target = target.setdefault(key, {})
            # Add value all the way down the branch under it's lowest-level key
            target[keys[-1]] = value

        self.data = self.parse_struct(struct, parse_map)
        return self

    def __repr__(self):
        return str(self.data)

    def __bytes__(self):
        lines = self.serialize_struct(self.data)
        return b'\n'.join(lines)

    def __len__(self):
        return len(bytes(self))

    def __eq__(self, other: object):
        return isinstance(other, Payload) and other.data == self.data

    def __getitem__(self, item: str):
        return self.data[item]

    def __setitem__(self, key: str, value: Union[PayloadValue, PayloadStruct]):
        self.data[key] = value

    def update(self, **kwargs: Union[PayloadValue, PayloadStruct]) -> None:
        self.data.update(**kwargs)

    def pop(self, key: str) -> PayloadValue:
        return self.data.pop(key)

    def keys(self) -> List[str]:
        return list(self.data.keys())

    def get(self, key: str, default: Optional[bytes] = None) -> Optional[Union[PayloadValue, PayloadStruct]]:
        return self.data.get(key, default)

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value = self.get(key)
        if value is None:
            return default

        if isinstance(value, bytes):
            value = value.decode(ENCODING)

        return self.unquote(str(value))

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        value = self.get(key)
        if value is None:
            return default

        if isinstance(value, bytes):
            value = value.decode(ENCODING)

        return int(value)

    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        value = self.get(key)
        if value is None:
            return default

        if isinstance(value, bytes):
            value = value.decode(ENCODING)

        return float(value)

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        value = self.get(key)
        if value is None:
            return default

        if isinstance(value, bytes):
            value = value.decode(ENCODING)

        if isinstance(value, str):
            return self.str_to_bool(value)

        return bool(value)

    def get_list(
            self,
            key: str,
            default: Optional[List[Union[PayloadValue, PayloadStruct]]] = None,
    ) -> Optional[List[Union[PayloadValue, PayloadStruct]]]:
        value = self.get(key)
        if value is None:
            return default

        if not isinstance(value, list):
            raise Error('Tried to get non-list payload value as list')

        return value

    def get_map(self, key: str, default: Optional[ParsedPayloadStruct] = None) -> Optional[ParsedPayloadStruct]:
        return self.get_dict(key, default)

    def get_dict(self, key: str, default: Optional[ParsedPayloadStruct] = None) -> Optional[ParsedPayloadStruct]:
        value = self.get(key)
        if value is None:
            return default

        if not isinstance(value, dict):
            raise Error('Tried to get non-dict payload value as dict')

        return value

    @staticmethod
    def parse_struct(struct: ParsedPayloadStruct, parse_map: Optional[ParseMap]) -> PayloadStruct:
        struct_type = Payload.determine_struct_type(struct)
        parsed = dict()
        for key, value in struct.items():
            if isinstance(value, dict):
                parsed[key] = Payload.parse_struct(value, parse_map)
            else:
                parsed[key] = Payload.parse_value(key, value, struct_type, parse_map)

        if struct_type is StructType.list:
            return Payload.struct_to_list(parsed)
        if struct_type is StructType.map:
            return Payload.struct_to_map(parsed)
        return parsed

    @staticmethod
    def determine_struct_type(struct: ParsedPayloadStruct) -> StructType:
        if StructLengthIndicator.list in struct:
            return StructType.list

        if StructLengthIndicator.map in struct:
            return StructType.map

        return StructType.struct

    @staticmethod
    def struct_to_list(struct: ParsedPayloadStruct) -> List[Union[bytes, ParsedPayloadStruct]]:
        length = Payload.get_struct_length(struct, StructLengthIndicator.list)
        if length == -1:
            raise ParameterError('Cannot convert non-list-struct to list')

        values = []
        for index in range(length):
            value = struct.get(str(index))
            if value is None:
                raise Error('Inconsistent payload list (missing index)')

            values.append(value)

        return values

    @staticmethod
    def struct_to_map(struct: ParsedPayloadStruct) -> ParsedPayloadStruct:
        length = Payload.get_struct_length(struct, StructLengthIndicator.map)
        if length == -1:
            raise ParameterError('Cannot convert non-map-struct to map')

        # Struct should contain the specified number of items plus the length indicator
        if len(struct) != length + 1:
            raise Error('Inconsistent payload map (length mismatch)')

        values = dict()
        for key, value in struct.items():
            if key != StructLengthIndicator.map:
                values[Payload.strip_map_key(key)] = value

        return values

    @staticmethod
    def parse_value(key: str, value: bytes, struct_type: StructType, parse_map: Optional[ParseMap]) -> PayloadValue:
        map_key = Payload.get_parse_map_key(key, struct_type, parse_map)
        if parse_map is None or map_key not in parse_map:
            return value

        target = parse_map[map_key]
        if target == str:
            return Payload.parse_str(value)
        if target == int:
            return Payload.parse_int(value)
        if target == float:
            return Payload.parse_float(value)
        if target == bool:
            return Payload.parse_bool(value)

        return value

    @staticmethod
    def get_parse_map_key(key: str, struct_type: StructType, parse_map: Optional[ParseMap]) -> str:
        # Scalar list keys are just the index, so allow a "magic key" to be specified to avoid
        # having to specify every index in the parse map (which would be impractical at best)
        if struct_type is StructType.list and key != StructLengthIndicator.list:
            return MagicParseKey.index

        # Map keys are wrapped in braces, e.g. {123456789}
        # => remove them to not have to include them in the parse map
        if struct_type is StructType.map and key != StructLengthIndicator.map:
            return Payload.strip_map_key(key)

        # Leaving any unknown keys unparsed may not always be practical, so allow another "magic key" to be specified
        # that determines a parse target type for any otherwise unmapped key (no need to check if fallback key is
        # actually in parse map, as it will skip parsing anyway if neither fallback nor key are in the parse map
        if parse_map is not None and key not in parse_map:
            return MagicParseKey.fallback

        return key

    @staticmethod
    def decode_and_parse(value: bytes, parse: Callable[[str], PayloadValue]) -> PayloadValue:
        try:
            as_str = value.decode(ENCODING)
            return parse(as_str)
        except (ValueError, UnicodeDecodeError) as e:
            raise Error(e) from None

    @staticmethod
    def parse_str(value: bytes) -> str:
        return Payload.decode_and_parse(value, Payload.unquote)

    @staticmethod
    def unquote(quoted: str) -> str:
        return unquote(quoted.strip('"'))

    @staticmethod
    def parse_int(value: bytes) -> int:
        return Payload.decode_and_parse(value, int)

    @staticmethod
    def parse_float(value: bytes) -> float:
        return Payload.decode_and_parse(value, float)

    @staticmethod
    def parse_bool(value: bytes) -> bool:
        as_str = Payload.parse_str(value)
        return Payload.str_to_bool(as_str)

    @staticmethod
    def str_to_bool(value: str) -> bool:
        if value in ['1', 'YES']:
            return True
        if value in ['0', 'NO']:
            return False

        # Raise error to adhere to behaviour of other parse methods
        raise Error(f'could not convert string to bool: \'{value}\'')

    @staticmethod
    def get_struct_length(data: ParsedPayloadStruct, indicator: Union[StructLengthIndicator, str]) -> int:
        return int(data.get(indicator, b'-1').decode(ENCODING))

    @staticmethod
    def serialize_struct(struct: PayloadStruct, *args: str) -> List[bytes]:
        if isinstance(struct, list):
            items = enumerate(struct)
            struct_type = StructType.list
        else:
            items = struct.items()
            struct_type = StructType.struct

        lines = []
        for key, value in items:
            if isinstance(value, dict) or isinstance(value, list):
                lines.extend(Payload.serialize_struct(value,  *args, key))
                continue

            path = Payload.build_path(*args, key)
            lines.append(Payload.serialize_item(path, value))

        if struct_type is StructType.list:
            length_indicator_path = Payload.build_path(*args, StructLengthIndicator.list)
            lines.append(Payload.serialize_item(length_indicator_path, len(struct)))

        return lines

    @staticmethod
    def serialize_item(path: str, value: PayloadValue) -> bytes:
        return b'='.join(map(Payload.encode, [path, value]))

    @staticmethod
    def encode(raw: Union[str, PayloadValue]) -> bytes:
        if isinstance(raw, bytes):
            return raw

        if isinstance(raw, bool):
            return Payload.encode(int(raw))

        if raw is None:
            return bytes()

        return str(raw).encode(ENCODING)

    @staticmethod
    def build_path(*args: Union[str, int]) -> str:
        return '.'.join(map(str, args))

    @staticmethod
    def destruct_path(path: str) -> List[str]:
        return path.split('.')

    @staticmethod
    def strip_map_key(key: str) -> str:
        """
        Remove '{}' from key, turning '{1032604717}' into '1032604717
        """
        return key.strip(StructLengthIndicator.map)
