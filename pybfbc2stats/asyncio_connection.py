import asyncio
import socket

from . import Connection
from .constants import BUFFER_SIZE
from .exceptions import PyBfbc2StatsTimeoutError, PyBfbc2StatsError


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
            raise PyBfbc2StatsError(f'Failed to connect to {self.host}:{self.port} ({e})')

    async def write(self, data: bytes) -> None:
        if not self.is_connected:
            await self.connect()

        try:
            self.writer.write(data)
            await self.writer.drain()
        except socket.error:
            raise PyBfbc2StatsError('Failed to send data to server')

    async def read(self) -> bytes:
        if not self.is_connected:
            await self.connect()

        buffer = b''
        receive_next = True
        while receive_next:
            try:
                iteration_buffer = await self.reader.read(BUFFER_SIZE - len(buffer))
            except socket.timeout:
                raise PyBfbc2StatsTimeoutError('Timed out while receiving server data')
            except socket.error:
                raise PyBfbc2StatsError('Failed to receive data from server')

            buffer += iteration_buffer

            receive_next = len(buffer) < BUFFER_SIZE and (len(buffer) == 0 or buffer[-1] != 0)

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
