from enum import Enum
from typing import Dict, Union, Optional, List, Callable, Type
from urllib.parse import unquote

from .constants import ENCODING
from .exceptions import Error, ParameterError

PayloadData = Dict[str, bytes]
StrValue = Union[str, bytes]
IntValue = Union[int, str, bytes]
FloatValue = Union[float, str, bytes]
PayloadValue = Optional[Union[StrValue, IntValue, FloatValue]]
PayloadStruct = Optional[Union[Dict[str, Union[PayloadValue, 'PayloadStruct']], List[Union[PayloadValue, 'PayloadStruct']]]]
ParseMap = Dict[str, Union[Type[str], Type[int], Type[float]]]
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


class MagicParseKey(str, Enum):
    index = '_index_'

    def __str__(self):
        return self.value


class Payload:
    data: PayloadData

    def __init__(self, **kwargs: Union[PayloadValue, PayloadStruct]):
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

    def __eq__(self, other):
        return isinstance(other, Payload) and other.data == self.data

    def __add__(self, other):
        if not isinstance(other, Payload):
            raise ParameterError(f'Cannot add {type(other)} to Payload')

        payload = Payload(**self.data)
        payload.update(**other.data)

        return payload

    def __iadd__(self, other):
        if not isinstance(other, Payload):
            raise ParameterError(f'Cannot add {type(other)} to Payload')

        self.data.update(**other.data)
        return self

    def update(self, **kwargs: Union[PayloadValue, PayloadStruct]) -> None:
        for key, value in kwargs.items():
            self.set(key, value)

    def set(self, key: str, value: Union[PayloadValue, PayloadStruct], *args: Union[str, int]) -> None:
        path = self.build_path(*args, key)

        # Ensure we remove any existing data under path (only run during base-level set)
        if len(args) == 0:
            self.remove(path)

        if isinstance(value, dict):
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
            self.data[path] = bytes()
            return

        # TODO Quote values
        self.data[path] = str(value).encode(ENCODING)

    def remove(self, key: str) -> None:
        # Cast to list to be able to change keys in loop (avoid dict size changed during iteration)
        for item_key in self.filter_by_path(self.data, key):
            self.data.pop(item_key)

    def get(self, key: str, default: Optional[bytes] = None) -> Optional[bytes]:
        return self.data.get(key, default)

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value = self.get(key)
        if value is None:
            return default

        return self.unquote(value.decode(ENCODING))

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

    def get_list(
            self,
            key: str,
            default: Optional[List[Union[bytes, ParsedPayloadStruct]]] = None,
            parse_map: Optional[ParseMap] = None
    ) -> Optional[List[Union[PayloadValue, PayloadStruct]]]:
        if not self.has_values_at_path(self.data, key):
            return default

        as_struct = self.get_struct(key, parse_map)
        return self.struct_to_list(as_struct)

    def get_map(
            self,
            key: str,
            default: Optional[ParsedPayloadStruct] = None,
            parse_map: Optional[ParseMap] = None
    ) -> Optional[ParsedPayloadStruct]:
        if not self.has_values_at_path(self.data, key):
            return default

        as_struct = self.get_struct(key, parse_map)
        return self.struct_to_map(as_struct)

    def get_dict(
            self,
            key: str,
            default: Optional[ParsedPayloadStruct] = None,
            parse_map: Optional[ParseMap] = None
    ) -> Optional[ParsedPayloadStruct]:
        if not self.has_values_at_path(self.data, key):
            return default

        return self.get_struct(key, parse_map)

    def get_struct(self, path: str, parse_map: Optional[ParseMap]) -> ParsedPayloadStruct:
        keys = self.destruct_path(path)
        groups = self.group_by_path(self.data, path)
        struct_type = self.determine_struct_type(groups, path)
        values = dict()
        for group_path, group in groups.items():
            group_keys = self.destruct_path(group_path)
            if len(group_keys) == 1 and group_keys[0] == path:
                raise Error(f'Payload value at {path} is not a struct')

            """
            The key of struct itself should not part of the keys in the struct. Meaning for a struct containing 
            b'userInfo.0.namespace=PS3_SUB', the parsed struct should be {'0': {'namespace': b'PS3_SUB'}}. Thus, 
            the first path element (the struct key, b'userInfo')) needs to dropped.
            """
            target_key = self.build_path(*tuple(group_keys[len(keys):]))
            if len(group) > 1:
                # Item is a nested struct => recurse, add all (converting as needed)
                struct = self.get_struct(group_path, parse_map)
                if StructLengthIndicator.list in struct:
                    values[target_key] = self.struct_to_list(struct)
                elif StructLengthIndicator.map in struct:
                    values[target_key] = self.struct_to_map(struct)
                else:
                    values[target_key] = struct
            elif len(group) == 1:
                # Only one item under path => scalar list, add value directly
                value = list(group.values()).pop()
                values[target_key] = self.parse(target_key, value, struct_type, parse_map)
            else:
                # An empty group should not be possible, so this error should never be raised
                raise Error(f'Payload struct at {path} is missing an item at {group_path}')

        return values

    @staticmethod
    def filter_by_path(data: PayloadData, path: str) -> Dict[str, bytes]:
        keys = Payload.destruct_path(path)
        matches = dict()
        for item_path, item_value in data.items():
            item_keys = Payload.destruct_path(item_path)
            if item_keys[:len(keys)] == keys:
                matches[item_path] = item_value

        return matches

    @staticmethod
    def group_by_path(data: PayloadData, path: str) -> Dict[str, PayloadData]:
        keys = Payload.destruct_path(path)
        items = Payload.filter_by_path(data, path)
        groups = dict()
        for item_path, item_value in items.items():
            item_keys = Payload.destruct_path(item_path)
            # Group path should be the struct path plus the next path element
            # e.g. for userInfo.0.namespace=PS3_SUB, all values under userInfo.0 should be grouped together
            group_path = Payload.build_path(*tuple(item_keys[:len(keys) + 1]))
            if group_path not in groups:
                groups[group_path] = dict()
            groups[group_path][item_path] = item_value

        return groups

    @staticmethod
    def determine_struct_type(groups: Dict[str, PayloadData], path: str) -> StructType:
        if Payload.build_list_length_path(path) in groups:
            return StructType.list

        if Payload.build_map_length_path(path) in groups:
            return StructType.map

        return StructType.struct

    @staticmethod
    def has_values_at_path(data: PayloadData, path: str) -> bool:
        group_paths = Payload.group_by_path(data, path).keys()
        return len(group_paths) >= 1

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
    def parse(key: str, value: bytes, struct_type: StructType, parse_map: Optional[ParseMap]) -> PayloadValue:
        map_key = Payload.get_parse_map_key(key, struct_type)
        if parse_map is None or map_key not in parse_map:
            return value

        target = parse_map[map_key]
        if target == str:
            return Payload.parse_str(value)
        if target == int:
            return Payload.parse_int(value)
        if target == float:
            return Payload.parse_float(value)

        return value

    @staticmethod
    def get_parse_map_key(key: str, struct_type: StructType) -> str:
        # Scalar list keys are just the index, so allow a "magic key" to be specified to avoid
        # having to specify every index in the parse map (which would be impractical at best)
        if struct_type is StructType.list and key != StructLengthIndicator.list:
            return MagicParseKey.index

        # Map keys are wrapped in braces, e.g. {123456789}
        # => remove them to not have to include them in the parse map
        if struct_type is StructType.map and key != StructLengthIndicator.map:
            return Payload.strip_map_key(key)

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
    def parse_int(value: bytes) -> int:
        return Payload.decode_and_parse(value, int)

    @staticmethod
    def parse_float(value: bytes) -> float:
        return Payload.decode_and_parse(value, float)

    @staticmethod
    def get_struct_length(
            data: Union[PayloadData, ParsedPayloadStruct],
            indicator: Union[StructLengthIndicator, str]
    ) -> int:
        return int(data.get(indicator, b'-1').decode(ENCODING))

    @staticmethod
    def build_path(*args: Union[str, int]) -> str:
        return '.'.join(map(str, args))

    @staticmethod
    def build_list_length_path(path: str) -> str:
        return Payload.build_path(path, StructLengthIndicator.list)

    @staticmethod
    def build_map_length_path(path: str) -> str:
        return Payload.build_path(path, StructLengthIndicator.map)

    @staticmethod
    def destruct_path(path: str) -> List[str]:
        return path.split('.')

    @staticmethod
    def strip_map_key(key: str) -> str:
        """
        Remove '{}' from key, turning '{1032604717}' into '1032604717
        """
        return key.strip(StructLengthIndicator.map)

    @staticmethod
    def unquote(quoted: str) -> str:
        return unquote(quoted.strip('"'))
