import socket
import ssl
import threading
import time
from typing import Sequence, Tuple, Type, Set

from .buffer import Buffer
from .constants import DNS_OVERRIDES
from .exceptions import TimeoutError, ConnectionError
from .logger import logger
from .packet import Packet


class Connection:
    host: str
    port: int
    packet_type: Type[Packet]
    timeout: float

    sock: socket.socket
    is_connected: bool = False
    # Number of times the connection has been established, allows telling apart data from before/after a reconnect
    generation: int = 0

    write_lock: threading.Lock
    stop_event: threading.Event

    def __init__(self, host: str, port: int, packet_type: Type[Packet], timeout: float = 2.0):
        self.host = host
        self.port = port
        self.packet_type = packet_type
        self.timeout = timeout
        self.write_lock = threading.Lock()
        self.stop_event = threading.Event()

    def connect(self) -> None:
        if self.is_connected:
            return

        # Manually resolve hostname to a) be able to log hostname and address and b) handle Xbox 360 DNS override
        address = self.resolve_host(self.host)

        target = self.format_target(self.host, address, self.port)
        logger.debug(f'Connecting to {target}')

        # Init socket
        self.sock = self.init_socket()

        try:
            self.sock.connect((address, self.port))
            self.is_connected = True
            self.generation = (self.generation + 1) % 2**32
        except socket.timeout:
            self.is_connected = False
            raise TimeoutError(f'Connection attempt to {target} timed out') from None
        except (socket.error, ConnectionResetError) as e:
            self.is_connected = False
            raise ConnectionError(f'Failed to connect to {target} ({e})') from None

    def write(self, packet: Packet) -> None:
        self.write_all([packet])

    def write_all(self, packets: Sequence[Packet]) -> None:
        """
        Write packets back to back, without any other packets being written in between. Required for multi-packet
        requests, since (at least some) backends cannot handle the packets of different requests being interleaved.
        """
        # Connect while holding the lock, so parallel first writes cannot each establish their own connection
        with self.write_lock:
            if not self.is_connected:
                logger.debug('Socket is not connected yet, connecting now')
                self.connect()

            logger.debug('Writing to socket')

            try:
                for packet in packets:
                    self.sock.sendall(bytes(packet))
                    logger.debug(packet)
            except (socket.error, ConnectionResetError, RuntimeError) as e:
                raise ConnectionError(f'Failed to send data to server ({e})') from None

    def read(self, wait: bool = False) -> Tuple[int, Packet]:
        """
        Read a single packet
        :param wait: Wait indefinitely for the first bytes of the packet (timeout only applies once data is arriving).
        Waiting is cancelled by stop_event
        """
        if not self.is_connected:
            logger.debug('Socket is not connected yet, connecting now')
            self.connect()

        logger.debug('Reading from socket')

        packet = self.packet_type()
        generations: Set[int] = set()
        last_received = time.time()
        timed_out = False
        while (packet_buflen := packet.buflen()) > 0 and not timed_out:
            try:
                generation, buffer = self.read_safe(packet_buflen)
            except TimeoutError:
                # Idle connection (no data of the packet received yet), keep waiting unless told to stop
                if wait and len(packet.header) == 0 and not self.stop_event.is_set():
                    continue
                raise

            generations.add(generation)
            if len(generations) > 1:
                raise ConnectionError('Connection was re-established while reading packet')

            # Append whatever data is missing from the head to it
            if (header_buflen := packet.header_buflen()) > 0:
                packet.header += buffer.read(min(header_buflen, buffer.length))
                # Log packet header once complete
                if packet.header_buflen() == 0:
                    logger.debug(f'Received header: {packet.header}')

                    # Make sure packet header is valid (throws exception if invalid)
                    packet.validate_header()

            # Append any remaining data to body
            packet.body += buffer.remaining()

            # Update timestamp if any data was retrieved during current iteration
            if buffer.length > 0:
                last_received = time.time()
            timed_out = time.time() > last_received + self.timeout

        if timed_out:
            raise TimeoutError('Timed out while reading packet header')

        logger.debug(f'Received body: {packet.body}')

        # Validate packet body (throws exception if invalid)
        packet.validate_body()

        return generations.pop(), packet

    def read_safe(self, buflen: int) -> Tuple[int, Buffer]:
        generation = self.generation
        try:
            data = self.sock.recv(buflen)
        except socket.timeout:
            raise TimeoutError('Timed out while receiving server data') from None
        except (socket.error, ConnectionResetError) as e:
            raise ConnectionError(f'Failed to receive data from server ({e})') from None

        if len(data) == 0:
            # EOF, remote end closed the connection
            self.is_connected = False
            raise ConnectionError('Server closed the connection')

        return generation, Buffer(data)

    def init_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        return sock

    @staticmethod
    def resolve_host(host: str) -> str:
        # Handle DNS overrides (required for Xbox 360 FESL and Theater, for which hostnames resolve to private IPs)
        if (address := DNS_OVERRIDES.get(host)) is not None:
            logger.debug(f'Overriding hostname resolution for {host} to resolve to {address}')
            return address

        try:
            address = socket.gethostbyname(host)
        except socket.gaierror:
            raise ConnectionError(f'Unable to resolve hostname ({host})') from None

        # IP addresses will resolve "to themselves", no need to log that
        if host != address:
            logger.debug(f'Hostname {host} resolved to {address}')

        return address

    @staticmethod
    def format_target(host: str, address: str, port: int) -> str:
        if host != address:
            return f'{host} ({address}) : {port}'
        else:
            return f'{host} : {port}'

    def __del__(self):
        self.close()

    def close(self) -> None:
        if hasattr(self, 'sock') and isinstance(self.sock, socket.socket):
            if self.is_connected:
                self.shutdown()
            self.sock.close()
            self.is_connected = False

    def shutdown(self) -> None:
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass


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
        context.minimum_version = ssl.TLSVersion.SSLv3
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers(':HIGH:!DH:!aNULL:RC4-SHA:RC4-MD5:@SECLEVEL=0')

        return context

    def close(self) -> None:
        if hasattr(self, 'sock') and isinstance(self.sock, ssl.SSLSocket):
            if self.is_connected:
                self.shutdown()
            self.sock.close()
            self.is_connected = False
