import asyncio
import socket
import time
from typing import Tuple

from .connection import Connection, SecureConnection
from .constants import HEADER_LENGTH, HEADER_ONLY_PACKET_HEADERS
from .exceptions import PyBfbc2StatsTimeoutError, PyBfbc2StatsConnectionError
from .logger import logger
from .packet import Packet


class AsyncConnection(Connection):
    sock: socket.socket
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    def __init__(self, host: str, port: int, timeout: float = 2.0):
        super().__init__(host, port, timeout)

    async def connect(self) -> None:
        if self.is_connected:
            return

        # Init socket
        self.sock = self.init_socket()

        try:
            self.sock.connect((self.host, self.port))
            self.reader, self.writer = await self.open_connection()
            self.is_connected = True
        except socket.timeout:
            self.is_connected = False
            raise PyBfbc2StatsTimeoutError(f'Connection attempt to {self.host}:{self.port} timed out')
        except socket.error as e:
            self.is_connected = False
            raise PyBfbc2StatsConnectionError(f'Failed to connect to {self.host}:{self.port} ({e})')

    async def write(self, packet: Packet) -> None:
        logger.debug('Writing to socket')
        if not self.is_connected:
            logger.debug('Socket is not connected yet, connecting now')
            await self.connect()

        try:
            self.writer.write(bytes(packet))
            await self.writer.drain()
        except socket.error:
            raise PyBfbc2StatsConnectionError('Failed to send data to server')

        logger.debug(packet)

    async def read(self) -> Packet:
        logger.debug('Reading from socket')
        if not self.is_connected:
            logger.debug('Socket is not connected yet, connecting now')
            await self.connect()

        # Read header only first
        logger.debug('Reading packet header')
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

        logger.debug(header)

        if timed_out:
            raise PyBfbc2StatsTimeoutError('Timed out while reading packet header')

        # Theater sends PING packets that do not have a body,
        # so skip body read for those in order to not read any data from the next packet
        if header not in HEADER_ONLY_PACKET_HEADERS:
            # Read remaining data as body until "eof" indicator (\x00)
            logger.debug('Reading packet body')
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

            logger.debug(body)
        else:
            logger.debug('Received header only packet, not reading any body data')
            body = b''

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

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        return await asyncio.open_connection(sock=self.sock)

    def __del__(self):
        pass

    async def close(self) -> bool:
        if hasattr(self, 'writer') and isinstance(self.writer, asyncio.StreamWriter):
            self.writer.close()
            await self.writer.wait_closed()
            self.is_connected = False
            return True

        return False


class AsyncSecureConnection(AsyncConnection):
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        context = SecureConnection.init_ssl_context()
        return await asyncio.open_connection(sock=self.sock, ssl=context, server_hostname=self.host)
