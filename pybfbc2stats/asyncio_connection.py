import asyncio
import socket

from .connection import Connection
from .constants import HEADER_LENGTH
from .exceptions import PyBfbc2StatsTimeoutError, PyBfbc2StatsConnectionError


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

    async def write(self, data: bytes) -> None:
        if not self.is_connected:
            await self.connect()

        try:
            self.writer.write(data)
            await self.writer.drain()
        except socket.error:
            raise PyBfbc2StatsConnectionError('Failed to send data to server')

    async def read(self) -> bytes:
        if not self.is_connected:
            await self.connect()

        # Read header only first
        header = b''
        while len(header) < HEADER_LENGTH:
            header += await self.reader.read(HEADER_LENGTH - len(header))

        # Read remaining data as body until "eof" indicator (\x00)
        body = b''
        receive_next = True
        while receive_next:
            try:
                iteration_buffer = await self.reader.readuntil(b'\x00')
            except socket.timeout:
                raise PyBfbc2StatsTimeoutError('Timed out while receiving server data')
            except socket.error:
                raise PyBfbc2StatsConnectionError('Failed to receive data from server')

            body += iteration_buffer

            receive_next = len(body) == 0 or body[-1] != 0

        return header + body

    def __del__(self):
        pass

    async def close(self) -> bool:
        if hasattr(self, 'writer') and isinstance(self.writer, asyncio.StreamWriter):
            self.writer.close()
            await self.writer.wait_closed()
            self.is_connected = False
            return True

        return False
