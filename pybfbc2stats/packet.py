from typing import List, Optional, Any

from .constants import HEADER_LENGTH, VALID_HEADER_TYPES_FESL, VALID_HEADER_TYPES_THEATER, \
    VALID_HEADER_ERROR_INDICATORS, HEADER_BYTE_ORDER, TransmissionType, FeslTransmissionType, TheaterTransmissionType
from .exceptions import Error


class Packet:
    header: bytes
    body: bytes

    def __init__(self, header: bytes = b'', body: bytes = b''):
        self.header = header
        self.body = body

    @classmethod
    def build(cls, header_stub: bytes, body_data: bytes, transmission_type: TransmissionType, tid: Optional[int] = None):
        """
        Build and return a new packet from a given header stub (first 8 header bytes) and the given body data
        :param header_stub: Packet header stub, consisting of at least the first 4 bytes
        :param body_data: Data to use as packet body
        :param transmission_type: Transmission type the packet is a part of (e.g. FeslTransmissionType.MultiPacketRequest)
        :param tid: Transaction id for packet
        :return: New packet with valid length indicators
        """

        """
        Add any missing header bytes as zero now and update later:
        - transmission type [1 byte]
        - tid [3 bytes, relevant only for FESL]
        - length indicator [4 bytes]
        """
        header = header_stub + b'\x00' * (HEADER_LENGTH - len(header_stub))
        # Add "tail" to body
        body = body_data + b'\n\x00'
        self = cls(header, body)
        # Update transaction id if given
        if tid is not None:
            self.set_tid(tid)
        # Update transmission type
        self.set_transmission_type(transmission_type)
        # Update length indicators
        self.set_length_indicators()
        return self

    def header_buflen(self) -> int:
        """Number of bytes to read until header is complete"""
        return HEADER_LENGTH - len(self.header)

    def body_buflen(self) -> int:
        """Number of bytes to read until body is complete"""
        return self.indicated_body_length() - len(self.body)

    def buflen(self) -> int:
        """Number of bytes to read until entire packet is complete"""
        # Remaining body buffer length may be unknown until we have a complete header, so complete that first
        if (header_buflen := self.header_buflen()) > 0:
            return header_buflen

        return self.body_buflen()

    def set_tid(self, tid: int) -> None:
        pass

    def get_tid(self) -> int:
        pass

    def set_transmission_type(self, transmission_type: TransmissionType) -> None:
        pass

    def get_transmission_type(self) -> TransmissionType:
        """Determine the type of transmission this packet is a part of based on the fifth header byte"""
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
        header_array[8:12] = self.int2bytes(packet_length)

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

    @staticmethod
    def int2bytes(i: int, length: int = 4):
        return int.to_bytes(i, length=length, byteorder=HEADER_BYTE_ORDER)

    def __str__(self):
        return (self.header + self.body).__str__()

    def __repr__(self):
        return str(self)

    def __bytes__(self):
        return self.header + self.body

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and \
               other.header == self.header and \
               other.body == self.body

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
        header_array[5:8] = self.int2bytes(tid, length=3)

        self.header = bytes(header_array)

    def get_tid(self) -> int:
        """
        Get transaction id from packet header
        :return: transaction id as int
        """
        return self.bytes2int(self.header[5:8])

    def set_transmission_type(self, transmission_type: TransmissionType) -> None:
        header_array = bytearray(self.header)
        if transmission_type is FeslTransmissionType.Ping:
            header_array[4:5] = b'\x00'
        elif transmission_type is FeslTransmissionType.SinglePacketResponse:
            header_array[4:5] = b'\x80'
        elif transmission_type is FeslTransmissionType.MultiPacketResponse:
            header_array[4:5] = b'\xb0'
        elif transmission_type is FeslTransmissionType.SinglePacketRequest:
            header_array[4:5] = b'\xc0'
        elif transmission_type is FeslTransmissionType.MultiPacketRequest:
            header_array[4:5] = b'\xf0'

        self.header = bytes(header_array)

    def get_transmission_type(self) -> TransmissionType:
        b = self.header[4:5]
        if b == b'\x00':
            return FeslTransmissionType.Ping
        elif b == b'\x80':
            return FeslTransmissionType.SinglePacketResponse
        elif b == b'\xb0':
            return FeslTransmissionType.MultiPacketResponse
        elif b == b'\xc0':
            return FeslTransmissionType.SinglePacketRequest
        elif b == b'\xf0':
            return FeslTransmissionType.MultiPacketRequest
        else:
            # Should never be raised, since packets are validated before accessing the transmission type
            raise Error('Unknown packet transmission type')

    def validate_header(self) -> None:
        super().validate_header()

        """
        Any valid FESL header also
        and
          starts with a valid data type (e.g. "rank") which is
          followed by a valid transmission type indicator:
            \x00 = ping packet
            \x80 = single packet response
            \xb0 = multi packet response
            \xc0 = single packet request
            \xf0 = multi packet request
        """
        valid = self.header[:4] in VALID_HEADER_TYPES_FESL and self.header[4] in [0, 128, 176, 192, 240]
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

    def set_transmission_type(self, transmission_type: TransmissionType) -> None:
        header_array = bytearray(self.header)
        # Cannot realistically set error response type here, since it could be any error
        if transmission_type is TheaterTransmissionType.Request:
            header_array[4:8] = b'@\x00\x00\x00'
        elif transmission_type is TheaterTransmissionType.OKResponse:
            header_array[4:8] = b'\x00\x00\x00\x00'

        self.header = bytes(header_array)

    def get_transmission_type(self) -> TransmissionType:
        b = self.header[4:8]
        if b == b'@\x00\x00\x00':
            return TheaterTransmissionType.Request
        elif b == b'\x00\x00\x00\x00':
            return TheaterTransmissionType.OKResponse
        elif b in VALID_HEADER_ERROR_INDICATORS:
            return TheaterTransmissionType.ErrorResponse
        else:
            # Should never be raised, since packets are validated before accessing the transmission type
            raise Error('Unknown packet transmission type')

    def validate_header(self) -> None:
        super().validate_header()

        """
        Any valid theater header also
        and
          starts with a valid data type (e.g. "GDAT") which is
          or
            followed by @\x00\x00\x00 (64 followed by 3 zero bytes, indicating a request)
            followed by \x00\x00\x00\x00 (4 zero bytes, indicating no-error/success response)
            followed by a valid 4-byte error response indicator (Theater indicates errors in header, not body)

        Theater error response packet headers are treated as valid here because we do need to read their body in order
        to not leave bytes "on the line". Also, they are not invalid responses just because they indicate an error.
        """
        valid = (self.header[:4] in VALID_HEADER_TYPES_THEATER and
                 (self.bytes2int(self.header[4:8]) == 0 or
                  self.header[4] == 64 and self.bytes2int(self.header[5:8]) == 0 or
                  self.header[4:8] in VALID_HEADER_ERROR_INDICATORS))

        if not valid:
            raise Error('Packet header is not valid')
