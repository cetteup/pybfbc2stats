import socket
import ssl

from .constants import BUFFER_SIZE
from .exceptions import PyBfbc2StatsTimeoutError, PyBfbc2StatsError


class Connection:
    __host: str
    __port: int
    __protocol: int
    __socket: ssl.SSLSocket
    __timeout: float
    __is_connected: bool = False

    def __init__(self, host: str, port: int, timeout: float = 2.0):
        self.__host = host
        self.__port = port
        self.__timeout = timeout

    def connect(self) -> None:
        if self.__is_connected:
            return

        # Init raw socket
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Init SSL context
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers(':HIGH:!DH:!aNULL')

        self.__socket = context.wrap_socket(raw_socket)

        self.__socket.settimeout(self.__timeout)

        try:
            self.__socket.connect((self.__host, self.__port))
            self.__is_connected = True
        except socket.timeout:
            self.__is_connected = False
            raise PyBfbc2StatsTimeoutError(f'Connection attempt to {self.__host}:{self.__port} timed out')
        except socket.error as e:
            self.__is_connected = False
            raise PyBfbc2StatsError(f'Failed to connect to {self.__host}:{self.__port} ({e})')

    def write(self, data: bytes) -> None:
        if not self.__is_connected:
            self.connect()

        try:
            self.__socket.sendall(data)
        except socket.error:
            raise PyBfbc2StatsError('Failed to send data to server')

    def read(self) -> bytes:
        if not self.__is_connected:
            self.connect()

        buffer = b''
        receive_next = True
        while receive_next:
            try:
                iteration_buffer = self.__socket.recv(BUFFER_SIZE)
            except socket.timeout:
                raise PyBfbc2StatsTimeoutError('Timed out while receiving server data')
            except socket.error:
                raise PyBfbc2StatsError('Failed to receive data from server')

            buffer += iteration_buffer

            receive_next = len(buffer) == 0 or buffer[-1] != 0

        return buffer

    def __del__(self):
        self.close()

    def close(self) -> bool:
        if hasattr(self, '__socket') and isinstance(self.__socket, socket.socket):
            if self.__is_connected:
                self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
            self.__is_connected = False
            return True

        return False
