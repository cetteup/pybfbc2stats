from typing import List

from .asyncio_connection import AsyncConnection
from .client import Client
from .constants import Step, Namespace, FESL_DETAILS, Platform, LookupType, DEFAULT_LEADERBOARD_KEYS, STATS_BUFFER_SIZE, \
    LEADERBOARD_BUFFER_SIZE
from .exceptions import PyBfbc2StatsNotFoundError


class AsyncClient(Client):
    connection: AsyncConnection

    def __init__(self, username: str, password: str, platform: Platform, timeout: float = 2.0,
                 track_steps: bool = True):
        super().__init__(username, password, platform, timeout=timeout, track_steps=track_steps)
        self.connection = AsyncConnection(FESL_DETAILS[self.platform]['host'], FESL_DETAILS[self.platform]['port'],
                                          timeout)

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

    async def lookup_usernames(self, usernames: List[str], namespace: Namespace) -> List[dict]:
        return await self.lookup_user_identifiers(usernames, namespace, LookupType.byName)

    async def lookup_username(self, username: str, namespace: Namespace) -> dict:
        return await self.lookup_user_identifier(username, namespace, LookupType.byName)

    async def lookup_user_ids(self, user_ids: List[int], namespace: Namespace) -> List[dict]:
        user_ids_str = [str(user_id) for user_id in user_ids]
        return await self.lookup_user_identifiers(user_ids_str, namespace, LookupType.byId)

    async def lookup_user_id(self, user_id: int, namespace: Namespace) -> dict:
        return await self.lookup_user_identifier(str(user_id), namespace, LookupType.byId)

    async def lookup_user_identifiers(self, identifiers: List[str], namespace: Namespace,
                                      lookup_type: LookupType) -> List[dict]:
        if self.track_steps and Step.login not in self.complete_steps:
            await self.login()

        lookup_packet = self.build_user_lookup_packet(identifiers, namespace, lookup_type)
        await self.connection.write(lookup_packet)
        response = await self.connection.read()
        body = response[12:-1]

        return self.parse_list_response(body, b'userInfo.')

    async def lookup_user_identifier(self, identifier: str, namespace: Namespace, lookup_type: LookupType) -> dict:
        results = await self.lookup_user_identifiers([identifier], namespace, lookup_type)

        if len(results) == 0:
            raise PyBfbc2StatsNotFoundError('User lookup did not return any results')

        return results.pop()

    async def get_stats(self, userid: int) -> dict:
        if self.track_steps and Step.login not in self.complete_steps:
            await self.login()

        # Send query in chunks
        chunk_packets = self.build_stats_query_packets(userid)
        for chunk_packet in chunk_packets:
            await self.connection.write(chunk_packet)

        parsed_response = await self.get_stats_response(STATS_BUFFER_SIZE, b'stats.')
        return self.dict_list_to_dict(parsed_response)

    async def get_stats_response(self, buffer_size: int, list_parse_prefix: bytes) -> List[dict]:
        response = b''
        last_packet = False
        while not last_packet:
            packet = await self.connection.read(buffer_size)
            data, last_packet = self.handle_stats_response_packet(packet, list_parse_prefix + b'[]=')
            response += data

        return self.parse_list_response(response, list_parse_prefix)
