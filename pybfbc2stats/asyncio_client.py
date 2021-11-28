from typing import List, Tuple, Optional

from .asyncio_connection import AsyncConnection
from .client import Client
from .constants import Step, Namespace, FESL_DETAILS, Platform, LookupType, DEFAULT_LEADERBOARD_KEYS, STATS_KEYS
from .exceptions import PyBfbc2StatsNotFoundError, PyBfbc2StatsLoginError


class AsyncClient(Client):
    connection: AsyncConnection

    def __init__(self, username: str, password: str, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        super().__init__(username, password, platform, timeout=timeout, track_steps=track_steps)
        self.connection = AsyncConnection(FESL_DETAILS[self.platform]['host'], FESL_DETAILS[self.platform]['port'],
                                          timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self.logout()
        await self.connection.close()

    async def hello(self) -> bytes:
        if self.track_steps and Step.hello in self.completed_steps:
            return bytes(self.completed_steps[Step.hello])

        hello_packet = self.build_hello_packet()
        await self.connection.write(hello_packet)

        # FESL sends hello response immediately followed initial memcheck => read both and return hello response
        response = await self.connection.read()
        _ = await self.connection.read()

        self.completed_steps[Step.hello] = hello_packet

        # Reply to initial memcheck
        await self.memcheck()

        return bytes(response)

    async def memcheck(self) -> None:
        memcheck_packet = self.build_memcheck_packet()
        await self.connection.write(memcheck_packet)

    async def login(self) -> bytes:
        if self.track_steps and Step.login in self.completed_steps:
            return bytes(self.completed_steps[Step.login])
        elif self.track_steps and Step.hello not in self.completed_steps:
            await self.hello()

        login_packet = self.build_login_packet(self.username, self.password)
        await self.connection.write(login_packet)
        response = await self.connection.read()

        response_valid, error_message = self.is_valid_login_response(response)
        if not response_valid:
            raise PyBfbc2StatsLoginError(error_message)

        self.completed_steps[Step.login] = response

        return bytes(response)

    async def logout(self) -> Optional[bytes]:
        # Only send logout if client is currently logged in
        if self.track_steps and Step.login in self.completed_steps:
            logout_packet = self.build_logout_packet()
            await self.connection.write(logout_packet)
            self.completed_steps.clear()
            return bytes(await self.connection.read())

    async def ping(self) -> None:
        ping_packet = self.build_ping_packet()
        await self.connection.write(ping_packet)

    async def get_lkey(self) -> bytes:
        if self.track_steps and Step.login not in self.completed_steps:
            await self.login()

        packet = self.completed_steps[Step.login]
        parsed = self.parse_simple_response(packet)

        return parsed['lkey']

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
        if self.track_steps and Step.login not in self.completed_steps:
            await self.login()

        lookup_packet = self.build_user_lookup_packet(identifiers, namespace, lookup_type)
        await self.connection.write(lookup_packet)

        parsed_response, *_ = await self.get_list_response(b'userInfo.')
        return parsed_response

    async def lookup_user_identifier(self, identifier: str, namespace: Namespace, lookup_type: LookupType) -> dict:
        results = await self.lookup_user_identifiers([identifier], namespace, lookup_type)

        if len(results) == 0:
            raise PyBfbc2StatsNotFoundError('User lookup did not return any results')

        return results.pop()

    async def search_name(self, screen_name: str, namespace: Namespace) -> dict:
        if self.track_steps and Step.login not in self.completed_steps:
            await self.login()

        search_packet = self.build_search_packet(screen_name, namespace)
        await self.connection.write(search_packet)

        parsed_response, metadata = await self.get_list_response(b'users.')
        return self.format_search_response(parsed_response, metadata)

    async def get_stats(self, userid: int, keys: List[bytes] = STATS_KEYS) -> dict:
        if self.track_steps and Step.login not in self.completed_steps:
            await self.login()

        # Send query in chunks
        chunk_packets = self.build_stats_query_packets(userid, keys)
        for chunk_packet in chunk_packets:
            await self.connection.write(chunk_packet)

        parsed_response, *_ = await self.get_list_response(b'stats.')
        return self.dict_list_to_dict(parsed_response)

    async def get_leaderboard(self, min_rank: int = 1, max_rank: int = 50, sort_by: bytes = b'score',
                              keys: List[bytes] = DEFAULT_LEADERBOARD_KEYS) -> List[dict]:
        if self.track_steps and Step.login not in self.completed_steps:
            await self.login()

        leaderboard_packet = self.build_leaderboard_query_packet(min_rank, max_rank, sort_by, keys)
        await self.connection.write(leaderboard_packet)

        parsed_response, *_ = await self.get_list_response(b'stats.')
        # Turn sub lists into dicts and return result
        return [{key: Client.dict_list_to_dict(value) if isinstance(value, list) else value
                 for (key, value) in persona.items()} for persona in parsed_response]

    async def get_list_response(self, list_entry_prefix: bytes) -> Tuple[List[dict], List[bytes]]:
        response = b''
        last_packet = False
        while not last_packet:
            packet = await self.connection.read()
            if b'TXN=MemCheck' in packet.body:
                # Respond to memcheck
                await self.memcheck()
            elif b'TXN=Ping' in packet.body:
                # Respond to ping
                await self.ping()
            else:
                data, last_packet = self.handle_list_response_packet(packet, list_entry_prefix)
                response += data

        return self.parse_list_response(response, list_entry_prefix)
