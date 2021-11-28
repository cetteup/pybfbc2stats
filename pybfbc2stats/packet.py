from typing import List

from .exceptions import PyBfbc2StatsError
from .constants import VALID_HEADER_TYPES


class Packet:
    header: bytes
    body: bytes

    def __init__(self, header: bytes, body: bytes):
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

    def validate(self) -> None:
        self.validate_header(self.header)
        self.validate_body(self.header, self.body)

    def get_data(self) -> bytes:
        """
        Get packet data (body without any trailing \x00 byte)
        """
        return self.body[:-1]

    def get_data_lines(self) -> List[bytes]:
        """
        Get packet data split into lines
        """
        return self.get_data().split(b'\n')

    def __str__(self):
        return (self.header + self.body).__str__()

    def __bytes__(self):
        return self.header + self.body

    @staticmethod
    def validate_header(header: bytes) -> None:
        """
        Make sure header
        a) starts with a valid type (e.g. "rank") which is
        b) followed by a valid packet count indicator (\x80 = single packet, \xb0 = multi packet) which is
        c) followed by \x00\x00
        """
        valid = header[:4] in VALID_HEADER_TYPES and header[4] in [176, 128] and header[5:7] == b'\x00\x00'
        if not valid:
            raise PyBfbc2StatsError('Packet header is not valid')

    @staticmethod
    def validate_body(header: bytes, body: bytes) -> None:
        # Sum of the last four header elements indicates the length of the entire packet
        # => validate indicators match total length of received data
        indicated_packet_length = (header[8] << 24) + (header[9] << 16) + (header[10] << 8) + header[11]
        actual_packet_length = len(header) + len(body)

        if indicated_packet_length != actual_packet_length:
            raise PyBfbc2StatsError('Received packet with invalid body')
