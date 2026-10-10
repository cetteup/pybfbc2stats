import inspect
import socket
import threading
import unittest
from typing import Callable

from pybfbc2stats import Platform, AsyncFeslClient, AsyncTheaterClient, FeslClient, TheaterClient, \
    AsyncRomeFeslClient, RomeFeslClient, AsyncRomeTheaterClient, RomeTheaterClient, Connection
from pybfbc2stats.constants import TheaterTransmissionType, TheaterStep
from pybfbc2stats.exceptions import ConnectionError
from pybfbc2stats.packet import TheaterPacket
from pybfbc2stats.payload import Payload


def run_in_threads(*targets: Callable[[], None]) -> None:
    """Run targets in parallel threads, raising (in the calling test) any exception that occurred in a thread"""
    errors = []

    def wrap(target: Callable[[], None]) -> Callable[[], None]:
        def run():
            try:
                target()
            except BaseException as e:
                errors.append(e)
        return run

    threads = [threading.Thread(target=wrap(target), daemon=True) for target in targets]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(5)
        if thread.is_alive():
            errors.append(AssertionError('Worker thread did not finish in time'))
    if errors:
        raise errors[0]


class FakeServer:
    def __init__(self, handler: Callable[[socket.socket], None], connections: int = 1):
        self.handler = handler
        self.connections = connections
        self.error = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('127.0.0.1', 0))
        self.sock.listen()
        self.port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self.serve, daemon=True)

    def serve(self):
        for _ in range(self.connections):
            try:
                conn, _ = self.sock.accept()
            except OSError:
                # Listening socket was closed
                return
            with conn:
                try:
                    self.handler(conn)
                except BaseException as e:
                    self.error = e

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *excinfo):
        self.sock.close()
        self.thread.join(5)
        # Only report handler errors if the test body itself did not already fail
        if excinfo[0] is None:
            self.assertion_check()

    def assertion_check(self):
        if self.error is not None:
            raise AssertionError(f'Fake server handler failed: {self.error!r}') from self.error
        if self.thread.is_alive():
            raise AssertionError('Fake server handler did not finish in time')


def theater_packet(command: bytes, tid: int, **kwargs) -> bytes:
    return bytes(TheaterPacket.build(command, Payload(TID=tid, **kwargs), TheaterTransmissionType.OKResponse, tid))


class TheaterClientLoopTest(unittest.TestCase):
    def test_responds_to_ping_while_idle(self):
        # GIVEN
        replies = []

        def handler(conn: socket.socket):
            conn.recv(4096)
            conn.sendall(theater_packet(b'CONN', 1))
            # Client is idle now, server pings it
            conn.sendall(bytes(TheaterPacket.build(b'PING', Payload(), TheaterTransmissionType.Request, 0)))
            replies.append(conn.recv(4096))
            conn.recv(4096)

        # WHEN
        with FakeServer(handler) as server:
            with TheaterClient('127.0.0.1', server.port, 'lkey', Platform.pc) as client:
                client.connect()
                server.thread.join(2)

                # THEN
                self.assertTrue(replies[0].startswith(b'PING'))

    def test_parallel_transactions(self):
        # GIVEN
        def handler(conn: socket.socket):
            # Respond to the second transaction first
            conn.sendall(theater_packet(b'LDAT', 2) + theater_packet(b'LDAT', 1))
            conn.recv(4096)

        # WHEN
        with FakeServer(handler) as server:
            with TheaterClient('127.0.0.1', server.port, 'lkey', Platform.pc) as client:
                client.connection.connect()
                with client.transaction() as first, client.transaction() as second:
                    packets = {}
                    run_in_threads(
                        lambda: packets.update({first: client.wrapped_read(first)}),
                        lambda: packets.update({second: client.wrapped_read(second)})
                    )

                # THEN
                self.assertEqual({1: 1, 2: 2}, {tid: packet.get_tid() for tid, (_, packet) in packets.items()})
                self.assertEqual({}, client.queues)

    def test_parallel_requests_perform_setup_steps_once(self):
        # GIVEN
        received = []

        def handler(conn: socket.socket):
            while data := conn.recv(4096):
                command = data[:4]
                received.append(command)
                tid = len(received)
                extra = {'NAME': 'some_persona'} if command == b'USER' else {}
                conn.sendall(theater_packet(command, tid, **extra))

        # WHEN
        with FakeServer(handler) as server:
            with TheaterClient('127.0.0.1', server.port, 'lkey', Platform.pc) as client:
                run_in_threads(*(client.authenticate for _ in range(5)))

        # THEN
        self.assertEqual([b'CONN', b'USER'], received)

    def test_connection_drop_fails_pending_requests_and_next_request_reconnects(self):
        # GIVEN
        received = []

        def handler(conn: socket.socket):
            data = conn.recv(4096)
            received.append(data[:4])
            if len(received) == 1:
                # First connection: Close without responding
                return
            conn.sendall(theater_packet(data[:4], len(received)))
            conn.recv(4096)

        # WHEN
        with FakeServer(handler, connections=2) as server:
            client = TheaterClient('127.0.0.1', server.port, 'lkey', Platform.pc, timeout=2.0)
            with client:
                # THEN
                with self.assertRaises(ConnectionError):
                    client.connect()

                # Failure of the previous read loop is not held against the next request
                client.connect()
                self.assertEqual([b'CONN', b'CONN'], received)
                self.assertTrue(client.completed_step(TheaterStep.conn))

    def test_steps_are_not_completed_after_connection_drop(self):
        # GIVEN
        received = []
        close = threading.Event()

        def handler(conn: socket.socket):
            data = conn.recv(4096)
            received.append(data[:4])
            conn.sendall(theater_packet(data[:4], len(received)))
            if len(received) == 1:
                # First connection: Close once told to
                close.wait(5)
                return
            conn.recv(4096)

        # WHEN
        with FakeServer(handler, connections=2) as server:
            client = TheaterClient('127.0.0.1', server.port, 'lkey', Platform.pc, timeout=2.0)
            with client:
                client.connect()
                self.assertTrue(client.completed_step(TheaterStep.conn))
                read_thread = client.read_thread
                close.set()
                read_thread.join(2)

                # THEN
                self.assertFalse(client.completed_step(TheaterStep.conn))
                client.connect()
                self.assertEqual([b'CONN', b'CONN'], received)
                self.assertTrue(client.completed_step(TheaterStep.conn))

    def test_exit_stops_reader_of_healthy_connection(self):
        # GIVEN
        def handler(conn: socket.socket):
            conn.recv(4096)
            conn.sendall(theater_packet(b'CONN', 1))
            conn.recv(4096)

        # WHEN
        with FakeServer(handler) as server:
            client = TheaterClient('127.0.0.1', server.port, 'lkey', Platform.pc, timeout=2.0)
            with client:
                client.connect()
                read_thread = client.read_thread

            # THEN
            self.assertFalse(read_thread.is_alive())


class ConnectionWriteTest(unittest.TestCase):
    def test_write_all_does_not_interleave(self):
        # GIVEN
        local, remote = socket.socketpair()
        connection = Connection('127.0.0.1', 0, TheaterPacket)
        connection.sock = local
        connection.is_connected = True

        def build(command: bytes, n: int):
            return [TheaterPacket.build(command, Payload(N=i), TheaterTransmissionType.Request, n) for i in range(20)]

        # WHEN
        run_in_threads(*(
            (lambda packets=build(command, n): connection.write_all(packets))
            for command, n in ((b'AAAA', 1), (b'BBBB', 2), (b'CCCC', 3))
        ))
        local.close()
        data = b''
        while chunk := remote.recv(65536):
            data += chunk
        remote.close()

        # THEN
        commands = [data[i:i + 4] for i in range(len(data)) if data[i:i + 4] in (b'AAAA', b'BBBB', b'CCCC')]
        # Collapse consecutive duplicates => every command must occur as exactly one uninterrupted run
        runs = [command for i, command in enumerate(commands) if i == 0 or commands[i - 1] != command]
        self.assertEqual(3, len(runs))


class ClientParityTest(unittest.TestCase):
    PAIRS = [
        (FeslClient, AsyncFeslClient),
        (TheaterClient, AsyncTheaterClient),
        (RomeFeslClient, AsyncRomeFeslClient),
        (RomeTheaterClient, AsyncRomeTheaterClient),
    ]
    EXCLUDED = {'__aenter__', '__aexit__', '__enter__', '__exit__'}

    @staticmethod
    def public_methods(cls) -> dict:
        return {
            name: list(inspect.signature(member).parameters.values())
            for name, member in inspect.getmembers(cls, inspect.isfunction)
            if (not name.startswith('_') or name.startswith('__')) and name not in ClientParityTest.EXCLUDED
        }

    def test_same_methods_and_signatures(self):
        for sync_cls, async_cls in self.PAIRS:
            with self.subTest(sync_cls.__name__):
                sync_methods = self.public_methods(sync_cls)
                async_methods = self.public_methods(async_cls)
                # Context managers of the async client are async-only, everything else must exist on both
                self.assertEqual(set(sync_methods) - {'__init__'}, set(async_methods) - {'__init__'})
                for name, signature in sync_methods.items():
                    self.assertEqual(signature, async_methods[name], name)

    def test_async_clients_reject_sync_with(self):
        for _, async_cls in ClientParityTest.PAIRS:
            with self.subTest(async_cls.__name__):
                with self.assertRaises(TypeError):
                    with async_cls.__new__(async_cls):
                        pass
