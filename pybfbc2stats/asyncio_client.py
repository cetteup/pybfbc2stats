from typing import List

from . import Client
from .asyncio_connection import AsyncConnection
from .client import Step
from .exceptions import PyBfbc2StatsNotFoundError


class AsyncClient(Client):
    connection: AsyncConnection

    def __init__(self, username: str, password: str, timeout: float = 2.0, track_steps: bool = True):
        super().__init__(username, password, timeout, track_steps)
        self.connection = AsyncConnection('bfbc2-pc-server.fesl.ea.com', 18321, timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self.connection.close()

    async def hello(self) -> bytes:
        if self.track_steps and Step.hello in self.complete_steps:
            return b''

        hello_packet = self.get_hello_packet()
        await self.connection.write(hello_packet)
        self.complete_steps.append(Step.hello)
        return await self.connection.read()

    async def memcheck(self) -> bytes:
        if self.track_steps and Step.memcheck in self.complete_steps:
            return b''
        elif self.track_steps and Step.hello not in self.complete_steps:
            await self.hello()

        memcheck_packet = self.get_memcheck_packet()
        await self.connection.write(memcheck_packet)
        self.complete_steps.append(Step.memcheck)
        return await self.connection.read()

    async def login(self) -> bytes:
        if self.track_steps and Step.login in self.complete_steps:
            return b''
        elif self.track_steps and Step.memcheck not in self.complete_steps:
            await self.memcheck()

        login_packet = self.build_login_packet(self.username, self.password)
        await self.connection.write(login_packet)
        self.complete_steps.append(Step.login)
        return await self.connection.read()

    async def lookup_usernames(self, usernames: List[str]) -> List[dict]:
        if self.track_steps and Step.login not in self.complete_steps:
            await self.login()

        lookup_packet = self.build_user_lookup_packet(usernames)
        await self.connection.write(lookup_packet)
        response = await self.connection.read()
        body = response[12:-1]

        return self.parse_list_response(body, b'userInfo.')

    async def lookup_username(self, username: str) -> dict:
        results = await self.lookup_usernames([username])

        if len(results) == 0:
            raise PyBfbc2StatsNotFoundError('Name lookup did not return any results')

        return results.pop()

    async def get_stats(self, userid: int) -> dict:
        if self.track_steps and Step.login not in self.complete_steps:
            await self.login()

        # Send query in chunks
        chunk_packets = self.build_stats_query_packets(userid)
        for chunk_packet in chunk_packets:
            await self.connection.write(chunk_packet)

        response = b''
        has_more_packets = True
        while has_more_packets:
            packet = await self.connection.read()
            data = self.handle_stats_response_packet(packet)
            response += data
            if data[-1:] == b'\x00':
                has_more_packets = False

        parsed = self.parse_list_response(response, b'stats.')
        return self.dict_list_to_dict(parsed)
