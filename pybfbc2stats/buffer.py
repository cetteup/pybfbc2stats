import struct
from enum import Enum
from typing import Union

from .exceptions import Error

class ByteOrder(str, Enum):
    LittleEndian = '<'
    BigEndian = '>'


class Buffer:
    data: bytes
    byte_order: ByteOrder

    length: int
    index: int
    reversed: bool

    def __init__(self, data: bytes = b'', byte_order: ByteOrder = ByteOrder.LittleEndian):
        self.data = data
        self.byte_order = byte_order

        self.length = len(data)
        self.index = 0
        self.reversed = False

    def __getitem__(self, key: Union[int, slice]) -> bytes:
        return self.data[key]

    def remaining(self) -> bytes:
        if self.reversed:
            return self.data[:self.index]
        return self.data[self.index:]

    def everything(self) -> bytes:
        return self.data

    def read(self, length: int = 1) -> bytes:
        if not self.reversed and self.index + length > self.length or self.reversed and self.index - length < 0:
            raise Error('Attempt to read beyond buffer length')

        remaining = self.remaining()
        self.shift(length)
        if self.reversed:
            data = remaining[-length:]
        else:
            data = remaining[:length]

        return data

    def peek(self, length: int = 1) -> bytes:
        remaining = self.remaining()
        if self.reversed:
            return remaining[-length:]
        return remaining[:length]

    def skip(self, length: int = 1) -> None:
        self.shift(length)

    def shift(self, length: int = 1) -> None:
        if self.reversed:
            self.index -= length
        else:
            self.index += length

    def reverse(self) -> None:
        """
        Reset the index and mark buffer to be read in reverse (index is reset to start/end)
        :return: None
        """
        self.reversed = not self.reversed
        self.index = self.length - self.index if self.reversed else self.index

    def read_ushort(self) -> int:
        v, *_ = struct.unpack(self.byte_order + 'H', self.read(2))
        return v
