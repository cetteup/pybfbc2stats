import asyncio
import socket
import threading
import unittest

from pybfbc2stats.asyncio_connection import AsyncConnection
from pybfbc2stats.connection import Connection
from pybfbc2stats.constants import TheaterTransmissionType
from pybfbc2stats.exceptions import ConnectionError
from pybfbc2stats.packet import TheaterPacket
from pybfbc2stats.payload import Payload


def packet_bytes(tid: int) -> bytes:
    return bytes(TheaterPacket.build(b'PING', Payload(TID=tid), TheaterTransmissionType.OKResponse, tid))


class ConnectionGenerationTest(unittest.TestCase):
    def serve(self, payload: bytes):
        server = socket.socket()
        server.bind(('127.0.0.1', 0))
        server.listen(5)
        self.addCleanup(server.close)

        def run():
            while True:
                try:
                    conn, _ = server.accept()
                except OSError:
                    return
                conn.sendall(payload)
                conn.close()

        threading.Thread(target=run, daemon=True).start()
        return server.getsockname()[1]

    def test_generation_counts_connects_and_is_returned_by_read(self):
        port = self.serve(packet_bytes(1))
        connection = Connection('127.0.0.1', port, TheaterPacket, 1.0)
        self.addCleanup(connection.close)
        self.assertEqual(0, connection.generation)

        connection.connect()
        generation, packet = connection.read()
        self.assertEqual((1, 1), (generation, packet.get_tid()))

        connection.close()
        connection.connect()
        generation, _ = connection.read()
        self.assertEqual(2, generation)

    def test_read_fails_if_generation_changes_while_reading(self):
        port = self.serve(packet_bytes(1))
        connection = Connection('127.0.0.1', port, TheaterPacket, 1.0)
        self.addCleanup(connection.close)
        connection.connect()
        original = connection.read_safe

        def read_safe(buflen):
            generation, buffer = original(buflen)
            connection.generation += 1
            return generation, buffer

        connection.read_safe = read_safe

        with self.assertRaises(ConnectionError):
            connection.read()


class AsyncConnectionGenerationTest(unittest.IsolatedAsyncioTestCase):
    async def test_generation_and_mismatch(self):
        async def handle(reader, writer):
            writer.write(packet_bytes(1))
            await writer.drain()
            writer.close()

        server = await asyncio.start_server(handle, '127.0.0.1', 0)
        self.addAsyncCleanup(server.wait_closed)
        self.addCleanup(server.close)
        port = server.sockets[0].getsockname()[1]
        connection = AsyncConnection('127.0.0.1', port, TheaterPacket, 1.0)
        self.addAsyncCleanup(connection.close)

        await connection.connect()
        generation, packet = await connection.read()
        self.assertEqual((1, 1), (generation, packet.get_tid()))

        await connection.close()
        await connection.connect()
        original = connection.read_safe

        async def read_safe(buflen, timeout=None):
            generation, buffer = await original(buflen, timeout)
            connection.generation += 1
            return generation, buffer

        connection.read_safe = read_safe
        with self.assertRaises(ConnectionError):
            await connection.read()
