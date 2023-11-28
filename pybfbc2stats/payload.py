from typing import Dict, Union, Optional, List

from .constants import ENCODING, StructLengthIndicator
from .exceptions import Error, ParameterError

PayloadData = Dict[str, bytes]
StrValue = Union[str, bytes]
IntValue = Union[int, str, bytes]
FloatValue = Union[float, str, bytes]
PayloadValue = Optional[Union[StrValue, IntValue, FloatValue]]
PayloadStruct = Optional[Union[Dict[str, Union[PayloadValue, 'PayloadStruct']], List[Union[PayloadValue, 'PayloadStruct']]]]
ParsedPayloadStruct = Dict[str, Union[bytes, List[Union[bytes, 'ParsedPayloadStruct']], 'ParsedPayloadStruct']]

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

    def get_list(self, key: str, default: Optional[List[Union[bytes, ParsedPayloadStruct]]] = None) -> Optional[List[Union[bytes, ParsedPayloadStruct]]]:
        if not self.has_values_at_path(self.data, key):
            return default

        as_struct = self.get_struct(key)
        return self.struct_to_list(as_struct)

    def get_map(self, key: str, default: Optional[ParsedPayloadStruct] = None) -> Optional[ParsedPayloadStruct]:
        if not self.has_values_at_path(self.data, key):
            return default

        as_struct = self.get_struct(key)
        return self.struct_to_map(as_struct)

    def get_dict(self, key: str, default: Optional[ParsedPayloadStruct] = None) -> Optional[ParsedPayloadStruct]:
        if not self.has_values_at_path(self.data, key):
            return default

        return self.get_struct(key)

    def get_struct(self, path: str) -> ParsedPayloadStruct:
        keys = self.destruct_path(path)
        groups = self.group_by_path(self.data, path)
        values = {}
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
                struct = self.get_struct(group_path)
                if StructLengthIndicator.list in struct:
                    values[target_key] = self.struct_to_list(struct)
                elif StructLengthIndicator.map in struct:
                    values[target_key] = self.struct_to_map(struct)
                else:
                    values[target_key] = struct
            elif len(group) == 1:
                # Only one item under path => scalar list, add value directly
                values[target_key] = list(group.values()).pop()
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

        values = {}
        for key, value in struct.items():
            if key != StructLengthIndicator.map:
                # Remove '{}' from key, turning '{1032604717}' into '1032604717
                values[key.strip(StructLengthIndicator.map)] = value

        return values

    @staticmethod
    def get_struct_length(data: Union[PayloadData, ParsedPayloadStruct], indicator: Union[StructLengthIndicator, str]) -> int:
        return int(data.get(indicator, b'-1').decode(ENCODING))

    @staticmethod
    def build_path(*args: Union[str, int]) -> str:
        return '.'.join(map(str, args))

    @staticmethod
    def build_list_length_path(path: str) -> str:
        return Payload.build_path(path, StructLengthIndicator.list)

    @staticmethod
    def destruct_path(path: str) -> List[str]:
        return path.split('.')
