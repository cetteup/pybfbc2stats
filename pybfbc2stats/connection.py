import logging
import socket
import ssl
import time

from .constants import HEADER_LENGTH, HEADER_ONLY_PACKET_HEADERS
from .exceptions import PyBfbc2StatsTimeoutError, PyBfbc2StatsConnectionError
from .packet import Packet


class Connection:
    host: str
    port: int
    sock: socket.socket
    timeout: float
    is_connected: bool = False

    def __init__(self, host: str, port: int, timeout: float = 2.0):
        self.host = host
        self.port = port
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
            raise PyBfbc2StatsTimeoutError(f'Connection attempt to {self.host}:{self.port} timed out')
        except socket.error as e:
            self.is_connected = False
            raise PyBfbc2StatsConnectionError(f'Failed to connect to {self.host}:{self.port} ({e})')

    def write(self, packet: Packet) -> None:
        logging.debug('Writing to socket')
        if not self.is_connected:
            logging.debug('Socket is not connected yet, connecting now')
            self.connect()

        try:
            self.sock.sendall(bytes(packet))
        except socket.error:
            raise PyBfbc2StatsConnectionError('Failed to send data to server')

        logging.debug(packet)

    def read(self) -> Packet:
        logging.debug('Reading from socket')
        if not self.is_connected:
            logging.debug('Socket is not connected yet, connecting now')
            self.connect()

        # Read header only first
        logging.debug('Reading packet header')
        header = b''
        last_received = time.time()
        timed_out = False
        while len(header) < HEADER_LENGTH and not timed_out:
            iteration_buffer = self.read_safe(HEADER_LENGTH - len(header))
            header += iteration_buffer

            # Update timestamp if any data was retrieved during current iteration
            if len(iteration_buffer) > 0:
                last_received = time.time()
            timed_out = time.time() > last_received + self.timeout

        if timed_out:
            raise PyBfbc2StatsTimeoutError('Timed out while reading packet header')

        logging.debug(header)

        # Theater sends PING packets that do not have a body,
        # so skip body read for those in order to not read any data from the next packet
        if header not in HEADER_ONLY_PACKET_HEADERS:
            # Read remaining data as body until "eof" indicator (\x00)
            logging.debug('Reading packet body')
            body = b''
            receive_next = True
            last_received = time.time()
            timed_out = False
            while receive_next and not timed_out:
                iteration_buffer = self.read_safe(1)
                body += iteration_buffer

                # Update timestamp if any data was retrieved during current iteration
                if len(iteration_buffer) > 0:
                    last_received = time.time()
                receive_next = len(body) == 0 or body[-1] != 0
                timed_out = time.time() > last_received + self.timeout

            logging.debug(body)
        else:
            logging.debug('Received header only packet, not reading any body data')
            body = b''

        if timed_out:
            raise PyBfbc2StatsTimeoutError('Timed out while reading packet body')

        # Init and validate packet (throws exception if invalid)
        packet = Packet(header, body)
        packet.validate()

        return packet

    def read_safe(self, buflen: int) -> bytes:
        try:
            buffer = self.sock.recv(buflen)
        except socket.timeout:
            raise PyBfbc2StatsTimeoutError('Timed out while receiving server data')
        except socket.error:
            raise PyBfbc2StatsConnectionError('Failed to receive data from server')

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

