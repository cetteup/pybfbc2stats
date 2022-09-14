import asyncio
import socket
import time
from typing import Tuple, Type

from .connection import Connection, SecureConnection
from .constants import HEADER_LENGTH
from .exceptions import TimeoutError, ConnectionError
from .logger import logger
from .packet import Packet


class AsyncConnection(Connection):
    sock: socket.socket
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    def __init__(self, host: str, port: int, packet_type: Type[Packet], timeout: float = 2.0):
        super().__init__(host, port, packet_type, timeout)

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
            raise TimeoutError(f'Connection attempt to {self.host}:{self.port} timed out')
        except (socket.error, ConnectionResetError) as e:
            self.is_connected = False
            raise ConnectionError(f'Failed to connect to {self.host}:{self.port} ({e})')

    async def write(self, packet: Packet) -> None:
        logger.debug('Writing to socket')
        if not self.is_connected:
            logger.debug('Socket is not connected yet, connecting now')
            await self.connect()

        try:
            self.writer.write(bytes(packet))
            await self.writer.drain()
        except (socket.error, ConnectionResetError, RuntimeError) as e:
            raise ConnectionError(f'Failed to send data to server ({e})')

        logger.debug(packet)

    async def read(self) -> Packet:
        logger.debug('Reading from socket')
        if not self.is_connected:
            logger.debug('Socket is not connected yet, connecting now')
            await self.connect()

        # Init empty packet
        packet = self.packet_type()

        # Read header only first
        logger.debug('Reading packet header')
        last_received = time.time()
        timed_out = False
        while len(packet.header) < HEADER_LENGTH and not timed_out:
            iteration_buffer = await self.read_safe(HEADER_LENGTH - len(packet.header))
            packet.header += iteration_buffer

            # Update timestamp if any data was retrieved during current iteration
            if len(iteration_buffer) > 0:
                last_received = time.time()
            timed_out = time.time() > last_received + self.timeout

        logger.debug(packet.header)

        # Make sure packet header is valid (throws exception if invalid)
        packet.validate_header()

        if timed_out:
            raise TimeoutError('Timed out while reading packet header')

        # Read number of bytes indicated by packet header
        logger.debug('Reading packet body')
        last_received = time.time()
        timed_out = False
        while len(packet.body) < packet.indicated_body_length() and not timed_out:
            iteration_buffer = await self.read_safe(packet.indicated_body_length() - len(packet.body))
            packet.body += iteration_buffer

            # Update timestamp if any data was retrieved during current iteration
            if len(iteration_buffer) > 0:
                last_received = time.time()
            timed_out = time.time() > last_received + self.timeout

        logger.debug(packet.body)

        if timed_out:
            raise TimeoutError('Timed out while reading packet body')

        # Validate packet body (throws exception if invalid)
        packet.validate_body()

        return packet

    async def read_safe(self, buflen: int) -> bytes:
        future = self.reader.read(buflen)
        try:
            buffer = await asyncio.wait_for(future, self.timeout)
        except (socket.timeout, asyncio.TimeoutError):
            raise TimeoutError('Timed out while receiving server data')
        except (socket.error, ConnectionResetError) as e:
            raise ConnectionError(f'Failed to receive data from server ({e})')

        return buffer

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        return await asyncio.open_connection(sock=self.sock)

    def __del__(self):
        pass

    async def close(self) -> bool:
        if hasattr(self, 'writer') and isinstance(self.writer, asyncio.StreamWriter):
            # We want to close the connection anyway, so catch and ignore any ConnectionResetError
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except ConnectionResetError:
                pass
            self.is_connected = False
            return True

        return False


class AsyncSecureConnection(AsyncConnection):
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        context = SecureConnection.init_ssl_context()
        return await asyncio.open_connection(sock=self.sock, ssl=context, server_hostname=self.host)
