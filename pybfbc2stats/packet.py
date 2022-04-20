from typing import List, Optional

from .constants import HEADER_LENGTH, VALID_HEADER_TYPES_FESL, VALID_HEADER_TYPES_THEATER, \
    VALID_HEADER_ERROR_INDICATORS, HEADER_BYTE_ORDER
from .exceptions import Error


class Packet:
    header: bytes
    body: bytes

    def __init__(self, header: bytes = b'', body: bytes = b''):
        self.header = header
        self.body = body

    @classmethod
    def build(cls, header_stub: bytes, body_data: bytes, tid: Optional[int] = None):
        """
        Build and return a new packet from a given header stub (first 8 header bytes) and the given body data
        :param header_stub: First 8 bytes of the packet header
        :param body_data: Data to use as packet body
        :param tid: Transaction id for packet
        :return: New packet with valid length indicators
        """
        # Add packet length indicators to header
        header = header_stub + b'\x00\x00\x00\x00'
        # Add "tail" to body
        body = body_data + b'\n\x00'
        self = cls(header, body)
        # Update transaction id if present
        if tid is not None:
            self.set_tid(tid)
        # Update length indicators
        self.set_length_indicators()
        return self

    def set_tid(self, tid: int) -> None:
        pass

    def get_tid(self) -> int:
        pass

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
        # Sum of the last four header elements indicates the length of the entire packet
        # => validate indicators match total length of received data
        return self.bytes2int(self.header[8:12])

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

    @staticmethod
    def bytes2int(b: bytes) -> int:
        return int.from_bytes(b, byteorder=HEADER_BYTE_ORDER)

    def __str__(self):
        return (self.header + self.body).__str__()

    def __bytes__(self):
        return self.header + self.body

    def validate_header(self) -> None:
        """
        Make sure every header
        and
          contains 12 bytes
          contains a non-zero packet body indicator
        """
        if not len(self.header) == HEADER_LENGTH or self.bytes2int(self.header[8:12]) <= 0:
            raise Error('Packet header is not valid')

    def validate_body(self) -> None:
        # Validate indicated length matches total length of received data
        if self.indicated_length() != len(self.header) + len(self.body):
            raise Error('Received packet with invalid body')


class FeslPacket(Packet):
    def set_tid(self, tid: int) -> None:
        """
        Set/update the transaction id/packet counter in packet header
        """
        # Deconstruct header bytes into bytearray
        header_array = bytearray(self.header)

        # Update transaction id bytes
        header_array[5] = tid >> 16 & 255
        header_array[6] = tid >> 8 & 255
        header_array[7] = tid & 255

        self.header = bytes(header_array)

    def get_tid(self) -> int:
        """
        Get transaction id from packet header
        :return: transaction id as int
        """
        return self.bytes2int(self.header[5:8])

    def validate_header(self) -> None:
        super().validate_header()

        """
        Any valid FESL header also
        and
          starts with a valid type (e.g. "rank") which is
          followed by a valid packet count indicator (\x00 = ping packet, \x80 = single packet, \xb0 = multi packet)
        """
        valid = self.header[:4] in VALID_HEADER_TYPES_FESL and self.header[4] in [0, 128, 176]
        if not valid:
            raise Error('Packet header is not valid')


class TheaterPacket(Packet):
    def set_tid(self, tid: int) -> None:
        """
        Set/update the transaction id/packet counter in packet body (requires re-calculation of length indicators)
        """
        # Remove body "tail", add tid and add "tail" again
        self.body = self.body[:-2] + b'\nTID=' + str(tid).encode('utf8') + b'\n\x00'

    def get_tid(self) -> int:
        """
        Get transaction id from packet body
        :return: transaction id as int
        """
        lines = self.get_data_lines()
        tid_line = next((line for line in lines if b'TID=' in line), b'')
        tid_bytes = tid_line[4:]

        if not tid_bytes.isalnum():
            return 0

        return int(tid_bytes)

    def validate_header(self) -> None:
        super().validate_header()

        """
        Any valid theater header also
        and
          starts with a valid type (e.g. "GDAT") which is
          or
            followed by \x00\x00\x00\x00 (4 zero bytes, indicating no-error/success)
            followed by a valid 4-byte error indicator (Theater indicates errors in header, not body)

        Theater error response packet headers are treated as valid here because we do need to read their body in order
        to not leave bytes "on the line". Also, they are not invalid responses just because they indicate an error.
        """
        valid = (self.header[:4] in VALID_HEADER_TYPES_THEATER and
                 (self.bytes2int(self.header[4:8]) == 0 or self.header[4:8] in VALID_HEADER_ERROR_INDICATORS))

        if not valid:
            raise Error('Packet header is not valid')
