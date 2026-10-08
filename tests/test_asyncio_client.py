import asyncio
import unittest

from pybfbc2stats import Platform
from pybfbc2stats.asyncio_client import AsyncTheaterClient
from pybfbc2stats.constants import TheaterTransmissionType
from pybfbc2stats.exceptions import ConnectionError
from pybfbc2stats.packet import TheaterPacket
from pybfbc2stats.payload import Payload


class AsyncTheaterClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_responds_to_ping_while_idle(self):
        # GIVEN
        replies = []
        replied = asyncio.Event()

        async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            await reader.read(4096)
            writer.write(bytes(TheaterPacket.build(b'CONN', Payload(TID=1), TheaterTransmissionType.OKResponse, 1)))
            await writer.drain()
            # Client is idle now, server pings it
            writer.write(bytes(TheaterPacket.build(b'PING', Payload(), TheaterTransmissionType.Request, 0)))
            await writer.drain()
            replies.append(await reader.read(4096))
            replied.set()
            writer.close()

        server = await asyncio.start_server(handle, '127.0.0.1', 0)
        port = server.sockets[0].getsockname()[1]
        client = AsyncTheaterClient('127.0.0.1', port, 'lkey', Platform.pc)

        # WHEN
        async with client:
            await client.connect()
            await asyncio.wait_for(replied.wait(), 2)

            # THEN
            self.assertTrue(replies[0].startswith(b'PING'))
            # Closed connection is reported to subsequent requests
            with self.assertRaises(ConnectionError):
                async with client.transaction() as tid:
                    await client.wrapped_read(tid)

        server.close()
        await server.wait_closed()

    async def test_parallel_transactions(self):
        # GIVEN
        async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            # Respond to the second transaction first
            for tid in (2, 1):
                packet = TheaterPacket.build(b'LDAT', Payload(TID=tid), TheaterTransmissionType.OKResponse, tid)
                writer.write(bytes(packet))
            await writer.drain()
            await reader.read()
            writer.close()

        server = await asyncio.start_server(handle, '127.0.0.1', 0)
        port = server.sockets[0].getsockname()[1]
        client = AsyncTheaterClient('127.0.0.1', port, 'lkey', Platform.pc)

        # WHEN
        async with client:
            await client.connection.connect()
            async with client.transaction() as first, client.transaction() as second:
                packets = await asyncio.gather(client.wrapped_read(first), client.wrapped_read(second))

            # THEN
            self.assertEqual([1, 2], [packet.get_tid() for packet in packets])
            self.assertEqual({}, client.queues)

        server.close()
        await server.wait_closed()

    async def test_parallel_requests_perform_setup_steps_once(self):
        # GIVEN
        received = []

        async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            while data := await reader.read(4096):
                command = data[:4]
                received.append(command)
                tid = len(received)
                payload = Payload(TID=tid, NAME='some_persona') if command == b'USER' else Payload(TID=tid)
                writer.write(bytes(TheaterPacket.build(command, payload, TheaterTransmissionType.OKResponse, tid)))
                await writer.drain()
            writer.close()

        server = await asyncio.start_server(handle, '127.0.0.1', 0)
        port = server.sockets[0].getsockname()[1]
        client = AsyncTheaterClient('127.0.0.1', port, 'lkey', Platform.pc)

        # WHEN
        async with client:
            await asyncio.gather(*(client.authenticate() for _ in range(3)))

        # THEN
        self.assertEqual([b'CONN', b'USER'], received)

        server.close()
        await server.wait_closed()
