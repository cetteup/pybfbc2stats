import socket
import ssl
import time
from typing import Type

from .constants import HEADER_LENGTH
from .exceptions import TimeoutError, ConnectionError
from .logger import logger
from .packet import Packet


class Connection:
    host: str
    port: int
    packet_type: Type[Packet]
    sock: socket.socket
    timeout: float
    is_connected: bool = False

    def __init__(self, host: str, port: int, packet_type: Type[Packet], timeout: float = 2.0):
        self.host = host
        self.port = port
        self.packet_type = packet_type
        self.timeout = timeout

    def connect(self) -> None:
        if self.is_connected:
            return

        # Init socket
        self.sock = self.init_socket()

        try:
            self.sock.connect((self.host, self.port))
            self.is_connected = True
        except socket.timeout:
            self.is_connected = False
            raise TimeoutError(f'Connection attempt to {self.host}:{self.port} timed out')
        except (socket.error, ConnectionResetError) as e:
            self.is_connected = False
            raise ConnectionError(f'Failed to connect to {self.host}:{self.port} ({e})')

    def write(self, packet: Packet) -> None:
        logger.debug('Writing to socket')
        if not self.is_connected:
            logger.debug('Socket is not connected yet, connecting now')
            self.connect()

        try:
            self.sock.sendall(bytes(packet))
        except (socket.error, ConnectionResetError, RuntimeError) as e:
            raise ConnectionError(f'Failed to send data to server ({e})')

        logger.debug(packet)

    def read(self) -> Packet:
        logger.debug('Reading from socket')
        if not self.is_connected:
            logger.debug('Socket is not connected yet, connecting now')
            self.connect()

        # Init empty packet
        packet = self.packet_type()

        # Read header only first
        logger.debug('Reading packet header')
        last_received = time.time()
        timed_out = False
        while len(packet.header) < HEADER_LENGTH and not timed_out:
            iteration_buffer = self.read_safe(HEADER_LENGTH - len(packet.header))
            packet.header += iteration_buffer

            # Update timestamp if any data was retrieved during current iteration
            if len(iteration_buffer) > 0:
                last_received = time.time()
            timed_out = time.time() > last_received + self.timeout

        if timed_out:
            raise TimeoutError('Timed out while reading packet header')

        logger.debug(packet.header)

        # Make sure packet header is valid (throws exception if invalid)
        packet.validate_header()

        # Read number of bytes indicated by packet header
        logger.debug('Reading packet body')
        last_received = time.time()
        timed_out = False
        while len(packet.body) < packet.indicated_body_length() and not timed_out:
            iteration_buffer = self.read_safe(packet.indicated_body_length() - len(packet.body))
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

    def read_safe(self, buflen: int) -> bytes:
        try:
            buffer = self.sock.recv(buflen)
        except socket.timeout:
            raise TimeoutError('Timed out while receiving server data')
        except (socket.error, ConnectionResetError) as e:
            raise ConnectionError(f'Failed to receive data from server ({e})')

        return buffer

    def init_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        return sock

    def __del__(self):
        self.close()

    def close(self) -> bool:
        if hasattr(self, 'sock') and isinstance(self.sock, socket.socket):
            if self.is_connected:
                self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.is_connected = False
            return True

        return False


class SecureConnection(Connection):
    sock: ssl.SSLSocket

    def init_socket(self) -> ssl.SSLSocket:
        raw_socket = super().init_socket()

        # Init SSL context
        context = self.init_ssl_context()

        return context.wrap_socket(raw_socket)

    @staticmethod
    def init_ssl_context():
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers(':HIGH:!DH:!aNULL')

        return context

    def close(self) -> bool:
        if hasattr(self, 'sock') and isinstance(self.sock, ssl.SSLSocket):
            if self.is_connected:
                self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.is_connected = False
            return True

        return False
