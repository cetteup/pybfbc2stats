import asyncio
import logging
import socket
import time

from .connection import Connection
from .constants import HEADER_LENGTH
from .exceptions import PyBfbc2StatsTimeoutError, PyBfbc2StatsConnectionError
from .packet import Packet


class AsyncConnection(Connection):
    tcp_socket: socket.socket
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    def __init__(self, host: str, port: int, timeout: float = 2.0):
        super().__init__(host, port, timeout)

    async def connect(self) -> None:
        if self.is_connected:
            return

        # Init raw socket
        self.tcp_socket = self.init_socket(self.timeout)

        # Init SSL context
        context = self.init_ssl_context()

        try:
            self.tcp_socket.connect((self.host, self.port))
            self.reader, self.writer = await asyncio.open_connection(sock=self.tcp_socket, ssl=context,
                                                                     server_hostname=self.host)
            self.is_connected = True
        except socket.timeout:
            self.is_connected = False
            raise PyBfbc2StatsTimeoutError(f'Connection attempt to {self.host}:{self.port} timed out')
        except socket.error as e:
            self.is_connected = False
            raise PyBfbc2StatsConnectionError(f'Failed to connect to {self.host}:{self.port} ({e})')

    async def write(self, packet: Packet) -> None:
        logging.debug('Writing to socket')
        if not self.is_connected:
            logging.debug('Socket is not connected yet, connecting now')
            await self.connect()

        try:
            self.writer.write(bytes(packet))
            await self.writer.drain()
        except socket.error:
            raise PyBfbc2StatsConnectionError('Failed to send data to server')

        logging.debug(packet)

    async def read(self) -> Packet:
        logging.debug('Reading from socket')
        if not self.is_connected:
            logging.debug('Socket is not connected yet, connecting now')
            await self.connect()

        # Read header only first
        logging.debug('Reading packet header')
        header = b''
        last_received = time.time()
        timed_out = False
        while len(header) < HEADER_LENGTH and not timed_out:
            iteration_buffer = await self.read_safe(HEADER_LENGTH - len(header))
            header += iteration_buffer

            # Update timestamp if any data was retrieved during current iteration
            if len(iteration_buffer) > 0:
                last_received = time.time()
            timed_out = time.time() > last_received + self.timeout

        logging.debug(header)

        if timed_out:
            raise PyBfbc2StatsTimeoutError('Timed out while reading packet header')

        # Read remaining data as body until "eof" indicator (\x00)
        logging.debug('Reading packet body')
        body = b''
        receive_next = True
        last_received = time.time()
        timed_out = False
        while receive_next and not timed_out:
            iteration_buffer = await self.read_safe_until(b'\x00')
            body += iteration_buffer

            # Update timestamp if any data was retrieved during current iteration
            if len(iteration_buffer) > 0:
                last_received = time.time()
            receive_next = len(body) == 0 or body[-1] != 0
            timed_out = time.time() > last_received + self.timeout

        logging.debug(body)

        if timed_out:
            raise PyBfbc2StatsTimeoutError('Timed out while reading packet body')

        # Init and validate packet (throws exception if invalid)
        packet = Packet(header, body)
        packet.validate()

        return packet

    async def read_safe(self, buflen: int) -> bytes:
        try:
            buffer = await self.reader.read(buflen)
        except socket.timeout:
            raise PyBfbc2StatsTimeoutError('Timed out while receiving server data')
        except socket.error:
            raise PyBfbc2StatsConnectionError('Failed to receive data from server')

        return buffer

    async def read_safe_until(self, separator: bytes) -> bytes:
        try:
            buffer = await self.reader.readuntil(separator)
        except socket.timeout:
            raise PyBfbc2StatsTimeoutError('Timed out while receiving server data')
        except socket.error:
            raise PyBfbc2StatsConnectionError('Failed to receive data from server')

        return buffer

    def __del__(self):
        pass

    async def close(self) -> bool:
        if hasattr(self, 'writer') and isinstance(self.writer, asyncio.StreamWriter):
            self.writer.close()
            await self.writer.wait_closed()
            self.is_connected = False
            return True

        return False
