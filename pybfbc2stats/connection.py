import socket
import ssl

from .constants import BUFFER_SIZE
from .exceptions import PyBfbc2StatsTimeoutError, PyBfbc2StatsError


class Connection:
    host: str
    port: int
    protocol: int
    ssl_socket: ssl.SSLSocket
    timeout: float
    is_connected: bool = False

    def __init__(self, host: str, port: int, timeout: float = 2.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    def connect(self) -> None:
        if self.is_connected:
            return

        # Init raw socket
        raw_socket = self.init_socket(self.timeout)

        # Init SSL context
        context = self.init_ssl_context()

        self.ssl_socket = context.wrap_socket(raw_socket)

        try:
            self.ssl_socket.connect((self.host, self.port))
            self.is_connected = True
        except socket.timeout:
            self.is_connected = False
            raise PyBfbc2StatsTimeoutError(f'Connection attempt to {self.host}:{self.port} timed out')
        except socket.error as e:
            self.is_connected = False
            raise PyBfbc2StatsError(f'Failed to connect to {self.host}:{self.port} ({e})')

    def write(self, data: bytes) -> None:
        if not self.is_connected:
            self.connect()

        try:
            self.ssl_socket.sendall(data)
        except socket.error:
            raise PyBfbc2StatsError('Failed to send data to server')

    def read(self) -> bytes:
        if not self.is_connected:
            self.connect()

        buffer = b''
        receive_next = True
        while receive_next:
            try:
                iteration_buffer = self.ssl_socket.recv(BUFFER_SIZE)
            except socket.timeout:
                raise PyBfbc2StatsTimeoutError('Timed out while receiving server data')
            except socket.error:
                raise PyBfbc2StatsError('Failed to receive data from server')

            buffer += iteration_buffer

            receive_next = len(buffer) == 0 or buffer[-1] != 0

        return buffer

    @staticmethod
    def init_socket(timeout: float) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        return sock

    @staticmethod
    def init_ssl_context():
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers(':HIGH:!DH:!aNULL')

        return context

    def __del__(self):
        self.close()

    def close(self) -> bool:
        if hasattr(self, 'ssl_socket') and isinstance(self.ssl_socket, socket.socket):
            if self.is_connected:
                self.ssl_socket.shutdown(socket.SHUT_RDWR)
            self.ssl_socket.close()
            self.is_connected = False
            return True

        return False
