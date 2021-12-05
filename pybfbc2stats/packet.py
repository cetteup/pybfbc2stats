from typing import List

from .exceptions import PyBfbc2StatsError
from .constants import VALID_HEADER_TYPES, HEADER_LENGTH


class Packet:
    header: bytes
    body: bytes

    def __init__(self, header: bytes = b'', body: bytes = b''):
        self.header = header
        self.body = body

    @classmethod
    def build(cls, header_stub: bytes, body_data: bytes):
        """
        Build and return a new packet from a given header stub (first 8 header bytes) and the given body data
        :param header_stub: First 8 bytes of the packet header
        :param body_data: Data to use as packet body
        :return: New packet with valid length indicators
        """
        # Add packet length indicators to header
        header = header_stub + b'\x00\x00\x00\x00'
        # Add "tail" to body
        body = body_data + b'\n\x00'
        self = cls(header, body)
        # Update length indicators
        self.set_length_indicators()
        return self

    def set_length_indicators(self) -> None:
        """
        Set/update length indicators in packet header
        """
        # Determine total length of packet
        packet_length = len(self.header) + len(self.body)

        # Deconstruct header bytes into bytearray
        header_array = bytearray(self.header)

        # Update length indicators
        header_array[8] = packet_length >> 24
        header_array[9] = packet_length >> 16
        header_array[10] = packet_length >> 8
        header_array[11] = packet_length & 255

        # Update header
        self.header = bytes(header_array)

    def indicated_length(self) -> int:
        # Make sure the header is valid first
        self.validate_header()
        # Sum of the last four header elements indicates the length of the entire packet
        # => validate indicators match total length of received data
        return (self.header[8] << 24) + (self.header[9] << 16) + (self.header[10] << 8) + self.header[11]

    def indicated_body_length(self) -> int:
        """
        Get length of packet body as indicated by header (total indicated length - header length)
        :return: Indicated and expected length of packet body
        """
        return self.indicated_length() - len(self.header)

    def validate(self) -> None:
        self.validate_header()
        self.validate_body()

    def get_data(self) -> bytes:
        """
        Get packet data (body without any trailing \x00 byte)
        """
        return self.body[:-1] if len(self.body) > 0 and self.body[-1] == 0 else self.body

    def get_data_lines(self) -> List[bytes]:
        """
        Get packet data split into lines
        """
        return self.get_data().split(b'\n')

    def __str__(self):
        return (self.header + self.body).__str__()

    def __bytes__(self):
        return self.header + self.body

    def validate_header(self) -> None:
        """
        Make sure header
        a) contains 12 bytes
        b) starts with a valid type (e.g. "rank") which is
        c) followed by a valid packet count indicator (\x80 = single packet, \xb0 = multi packet) which is
        d) followed by \x00\x00
        """
        valid = (len(self.header) == HEADER_LENGTH and self.header[:4] in VALID_HEADER_TYPES and
                 self.header[4] in [0, 128, 176] and self.header[5:7] == b'\x00\x00')
        if not valid:
            raise PyBfbc2StatsError('Packet header is not valid')

    def validate_body(self) -> None:
        # Validate indicated length matches total length of received data
        if self.indicated_length() != len(self.header) + len(self.body):
            raise PyBfbc2StatsError('Received packet with invalid body')
