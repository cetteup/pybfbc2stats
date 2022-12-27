import struct
from typing import Union

from .exceptions import Error


class Buffer:
    data: bytes
    length: int
    index: int

    def __init__(self, data: bytes = b''):
        self.data = data
        self.length = len(data)
        self.index = 0

    def __getitem__(self, key: Union[int, slice]) -> bytes:
        return self.data[key]

    def get_buffer(self) -> bytes:
        return self.data[self.index:]

    def read(self, length: int = 1) -> bytes:
        if self.index + length > self.length:
            raise Error('Attempt to read beyond buffer length')

        data = self.data[self.index:self.index + length]
        self.index += length

        return data
