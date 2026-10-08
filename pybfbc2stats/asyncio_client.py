import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, List, Tuple, Optional, Union

from .asyncio_connection import AsyncSecureConnection, AsyncConnection
from .client import Client, FeslClient, TheaterClient
from .constants import FeslStep, Namespace, Platform, LookupType, DEFAULT_LEADERBOARD_KEYS, STATS_KEYS, \
    TheaterStep, ENCODING, FeslParseMap, TheaterParseMap, Backend
from .exceptions import PlayerNotFoundError, AuthError, ConnectionError, TimeoutError
from .logger import logger
from .packet import Packet, FeslPacket, TheaterPacket
from .payload import Payload, StrValue, IntValue, ParseMap


class AsyncClient(Client):
    connection: AsyncConnection
    read_task = Optional[asyncio.Task]
    read_error = Optional[Exception]
    queues: dict[int, asyncio.Queue]

    def __init__(
            self,
            connection: AsyncConnection,
            platform: Platform,
            client_string: StrValue,
            timeout: float = 3.0,
            track_steps: bool = True
    ):
        super().__init__(connection, platform, client_string, timeout, track_steps)
        self.read_task = None
        self.read_error = None
        self.queues = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self.stop_read_loop()
        await self.connection.close()

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[int]:
        """
        Start a transaction, i.e. assign a transaction id and register a queue to receive the responses to it. Multiple
        transactions may be pending at the same time. The queue is removed once the transaction is done (or failed).
        """
        tid = self.get_transaction_id()
        self.queues[tid] = asyncio.Queue()
        try:
            yield tid
        finally:
            self.queues.pop(tid, None)

    def start_read_loop(self) -> None:
        if self.read_task is None:
            self.read_task = asyncio.create_task(self.read_loop())

    async def stop_read_loop(self) -> None:
        if self.read_task is not None:
            self.read_task.cancel()
            try:
                await self.read_task
            except asyncio.CancelledError:
                pass
            self.read_task = None
        self.read_error = None
        self.queues = {}

    async def read_loop(self) -> None:
        """
        Continuously read packets, respond to those that require an immediate response (memcheck, ping) and hand all
        others to the transaction waiting for them. This keeps the connection alive between requests.
        """
        try:
            while True:
                packet = await self.connection.read(wait=True)

                auto_respond, handler = self.is_auto_respond_packet(packet)
                if auto_respond:
                    await handler()
                    continue

                tid = packet.get_tid()
                if tid in self.queues:
                    self.queues[tid].put_nowait(packet)
                else:
                    logger.debug(f'Dropping packet that is not part of any current transaction (tid {tid})')
        except Exception as e:
            self.read_error = e
            for queue in self.queues.values():
                queue.put_nowait(e)

    async def wrapped_read(self, tid: int) -> Packet:
        queue = self.queues.get(tid)
        if queue is None:
            raise ConnectionError(f'No active transaction with id {tid}')

        self.start_read_loop()
        if self.read_error is not None and queue.empty():
            raise self.read_error

        try:
            item = await asyncio.wait_for(queue.get(), self.connection.timeout)
        except asyncio.TimeoutError:
            raise TimeoutError('Timed out while waiting for server response') from None

        if isinstance(item, Exception):
            raise item

        return item


class AsyncFeslClient(FeslClient, AsyncClient):
    connection: AsyncSecureConnection

    def __init__(self, username: StrValue, password: StrValue, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        host, port, client_string = self.get_backend_details(Backend.official, platform)
        connection = AsyncSecureConnection(host, port, FeslPacket, timeout)
        """
        Multiple inheritance works here, but only if we "skip" the FeslClient constructor. The method resolution here
        is: AsyncFeslClient, FeslClient, AsyncClient, Client. So, by calling super(), we would call the FeslClient
        __init__ function with parameters that make no sense. If we instead use super(FeslClient, self), we call
        FeslClient's super directly - effectively skipping the FeslClient constructor
        """
        super(FeslClient, self).__init__(connection, platform, client_string, timeout, track_steps)
        self.username = username
        self.password = password

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        try:
            await self.logout()
        except (ConnectionError, TimeoutError):
            pass
        await self.stop_read_loop()
        await self.connection.close()

    async def hello(self) -> bytes:
        if self.completed_step(FeslStep.hello):
            return bytes(self.completed_steps[FeslStep.hello])

        async with self.transaction() as tid:
            hello_packet = self.build_hello_packet(tid, self.client_string)
            await self.connection.write(hello_packet)

            # FESL sends hello response immediately followed by an initial memcheck, which the read loop responds to
            response = await self.wrapped_read(tid)

            self.completed_steps[FeslStep.hello] = response

            return bytes(response)

    async def memcheck(self) -> None:
        memcheck_packet = self.build_memcheck_packet()
        await self.connection.write(memcheck_packet)

    # TODO: Concurrent requests on a fresh client all see their setup steps (hello, login, login_persona) as not
    #  completed and would each run them (e.g. several logins at once). Guard hello/login/login_persona (and the Theater
    #  connect/authenticate steps) with an asyncio.Lock and re-check completed_step() once the lock is acquired, so
    #  the steps are only ever performed once.
    async def login(self, tos_version: Optional[StrValue] = None) -> bytes:
        if self.completed_step(FeslStep.login):
            return bytes(self.completed_steps[FeslStep.login])
        elif not self.completed_step(FeslStep.hello):
            await self.hello()

        async with self.transaction() as tid:
            login_packet = self.build_login_packet(tid, self.username, self.password, tos_version)
            await self.connection.write(login_packet)
            response = await self.wrapped_read(tid)

            response_valid, error_message, code = self.is_valid_login_response(response)
            if not response_valid:
                # If we received a "TOS Content is out of date" error, fetch current TOS version and try login one more time
                if code == 260 and tos_version is None and (tos_version := await self.get_tos_version()) != bytes():
                    return await self.login(tos_version)
                raise AuthError(error_message)

            self.completed_steps[FeslStep.login] = response

            return bytes(response)

    async def login_persona(self, persona_name: Optional[str] = None) -> bytes:
        if not self.completed_step(FeslStep.login):
            await self.login()

        # Fetch and use first available persona if none was given
        if persona_name is None:
            personas = await self.get_personas()
            if len(personas) < 1:
                raise AuthError("No persona available for login")

            persona_name = personas[0]

        async with self.transaction() as tid:
            login_persona_packet = self.build_persona_login_packet(tid, persona_name)
            await self.connection.write(login_persona_packet)
            response = await self.wrapped_read(tid)

            response_valid, error_message, _ = self.is_valid_login_response(response)
            if not response_valid:
                raise AuthError(error_message)

            self.completed_steps[FeslStep.login_persona] = response

            return bytes(response)

    async def logout(self) -> Optional[bytes]:
        # Only send logout if client is currently logged in
        if self.completed_step(FeslStep.login):
            async with self.transaction() as tid:
                logout_packet = self.build_logout_packet(tid)
                await self.connection.write(logout_packet)
                self.completed_steps.clear()
                return bytes(await self.wrapped_read(tid))

    async def ping(self) -> None:
        ping_packet = self.build_ping_packet()
        await self.connection.write(ping_packet)

    async def get_tos_version(self) -> bytes:
        if not self.completed_step(FeslStep.hello):
            await self.hello()

        async with self.transaction() as tid:
            packet = self.build_tos_packet(tid)
            await self.connection.write(packet)
            response = await self.get_response(tid)

            return response.get('version', bytes())

    async def get_theater_details(self) -> Tuple[str, int]:
        if not self.completed_step(FeslStep.hello):
            await self.hello()

        packet = self.completed_steps[FeslStep.hello]
        payload = packet.get_payload()

        # Field is called "ip" but actually contains the hostname
        return payload.get_str('theaterIp', str()), payload.get_int('theaterPort', int())

    async def get_lkey(self) -> str:
        if not self.completed_step(FeslStep.login):
            await self.login()

        packet = self.completed_steps[FeslStep.login]
        payload = packet.get_payload()

        return payload.get_str('lkey', str())

    async def get_personas(self) -> List[str]:
        if not self.completed_step(FeslStep.login):
            await self.login()

        async with self.transaction() as tid:
            packet = self.build_get_personas_packet(tid)
            await self.connection.write(packet)

            payload = await self.get_response(tid, parse_map=FeslParseMap.Personas)
            personas = payload.get_list('personas', list())
            return personas

    async def lookup_usernames(self, usernames: List[StrValue], namespace: Namespace) -> List[dict]:
        return await self.lookup_user_identifiers(usernames, namespace, LookupType.byName)

    async def lookup_username(self, username: StrValue, namespace: Namespace) -> dict:
        return await self.lookup_user_identifier(username, namespace, LookupType.byName)

    async def lookup_user_ids(self, user_ids: List[IntValue], namespace: Namespace) -> List[dict]:
        return await self.lookup_user_identifiers(user_ids, namespace, LookupType.byId)

    async def lookup_user_id(self, user_id: IntValue, namespace: Namespace) -> dict:
        return await self.lookup_user_identifier(user_id, namespace, LookupType.byId)

    async def lookup_user_identifiers(self, identifiers: List[Union[StrValue, IntValue]], namespace: Namespace,
                                      lookup_type: LookupType) -> List[dict]:
        if not self.completed_step(FeslStep.login):
            await self.login()

        async with self.transaction() as tid:
            lookup_packet = self.build_user_lookup_packet(tid, identifiers, namespace, lookup_type)
            await self.connection.write(lookup_packet)

            payload = await self.get_response(tid, parse_map=FeslParseMap.UserLookup)
            return payload.get_list('userInfo', list())

    async def lookup_user_identifier(self, identifier: Union[StrValue, IntValue], namespace: Namespace, lookup_type: LookupType) -> dict:
        results = await self.lookup_user_identifiers([identifier], namespace, lookup_type)

        if len(results) == 0:
            raise PlayerNotFoundError('User lookup did not return any results')

        return results.pop()

    async def search_name(self, screen_name: StrValue, namespace: Namespace) -> dict:
        if not self.completed_step(FeslStep.login):
            await self.login()

        async with self.transaction() as tid:
            search_packet = self.build_search_packet(tid, screen_name, namespace)
            await self.connection.write(search_packet)

            payload = await self.get_response(tid, parse_map=FeslParseMap.NameSearch)
            return {
                'namespace': payload.get_str('nameSpaceId', str()),
                'users': payload.get_list('users', list())
            }

    async def get_stats(self, userid: IntValue, keys: List[StrValue] = STATS_KEYS) -> dict:
        if not self.completed_step(FeslStep.login):
            await self.login()

        # Send query in chunks (using the same transaction id for all packets)
        # TODO: The connection's write lock is only held per packet, so chunks of concurrent requests may be interleaved
        #  on the wire. Test against the backend whether it handles that (chunks carry the transaction id). If it does
        #  not, send all chunks of a request while holding the write lock.
        async with self.transaction() as tid:
            chunk_packets = self.build_stats_query_packets(tid, userid, keys)
            for chunk_packet in chunk_packets:
                await self.connection.write(chunk_packet)

            payload = await self.get_response(tid, parse_map=FeslParseMap.Stats)
            return self.dict_list_to_dict(payload.get_list('stats', list()))

    async def get_leaderboard(self, min_rank: IntValue = 1, max_rank: IntValue = 50, sort_by: StrValue = 'score',
                              keys: List[StrValue] = DEFAULT_LEADERBOARD_KEYS) -> List[dict]:
        if not self.completed_step(FeslStep.login):
            await self.login()

        async with self.transaction() as tid:
            leaderboard_packet = self.build_leaderboard_query_packet(tid, min_rank, max_rank, sort_by, keys)
            await self.connection.write(leaderboard_packet)

            payload = await self.get_response(tid, parse_map=FeslParseMap.Leaderboard)
            # Turn sub lists into dicts and return result
            return [
                {
                    key: Client.dict_list_to_dict(value) if isinstance(value, list) else value
                    for (key, value) in entry.items()
                } for entry in payload.get_list('stats', list())
            ]

    async def get_dogtags(self, userid: IntValue) -> List[dict]:
        if not self.completed_step(FeslStep.login):
            await self.login()

        async with self.transaction() as tid:
            dogtags_packet = self.build_dogtag_query_packet(tid, userid)
            await self.connection.write(dogtags_packet)

            payload = await self.get_response(tid, parse_map=FeslParseMap.Dogtags)
            return self.format_dogtags_response(payload.get_map('values', dict()), self.platform)

    async def get_response(self, tid: int, parse_map: Optional[ParseMap] = None) -> Payload:
        response = bytes()
        last_packet = False
        while not last_packet:
            packet = await self.wrapped_read(tid)
            data, last_packet = self.process_response_packet(packet)
            response += data

        return Payload.from_bytes(response, parse_map)


class AsyncTheaterClient(TheaterClient, AsyncClient):
    def __init__(self, host: str, port: int, lkey: StrValue, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        connection = AsyncConnection(host, port, TheaterPacket)
        _, _, client_string = self.get_backend_details(Backend.official, platform)
        # "Skip" TheaterClient constructor, for details see note in AsyncFeslClient.__init__
        super(TheaterClient, self).__init__(connection, platform, client_string, timeout, track_steps)
        self.lkey = lkey

    async def connect(self) -> bytes:
        if self.completed_step(TheaterStep.conn):
            return bytes(self.completed_steps[TheaterStep.conn])

        async with self.transaction() as tid:
            connect_packet = self.build_conn_packet(tid, self.client_string)
            await self.connection.write(connect_packet)

            response = await self.wrapped_read(tid)
            self.completed_steps[TheaterStep.conn] = response

            return bytes(response)

    async def authenticate(self) -> bytes:
        if self.completed_step(TheaterStep.user):
            return bytes(self.completed_steps[TheaterStep.user])
        elif not self.completed_step(TheaterStep.conn):
            await self.connect()

        async with self.transaction() as tid:
            auth_packet = self.build_user_packet(tid, self.lkey)
            await self.connection.write(auth_packet)

            response = await self.wrapped_read(tid)

            if not self.is_valid_authentication_response(response):
                raise AuthError('Theater authentication failed')

            self.completed_steps[TheaterStep.user] = response

            return bytes(response)

    async def ping(self) -> None:
        ping_packet = self.build_ping_packet()
        await self.connection.write(ping_packet)

    async def get_lobbies(self) -> List[dict]:
        if not self.completed_step(TheaterStep.user):
            await self.authenticate()

        async with self.transaction() as tid:
            lobby_list_packet = self.build_llst_packet(tid)
            await self.connection.write(lobby_list_packet)

            # Theater responds with an initial LLST packet, indicating the number of lobbies,
            # followed by n LDAT packets with the lobby details
            llst_response = await self.wrapped_read(tid)
            llst = llst_response.get_payload()
            num_lobbies = llst.get_int('NUM-LOBBIES', int())

            # Retrieve given number of lobbies (usually just one these days)
            lobbies = []
            for i in range(num_lobbies):
                ldat_response = await self.wrapped_read(tid)
                ldat = ldat_response.get_payload(TheaterParseMap.LDAT)
                lobbies.append(dict(ldat))

            return lobbies

    async def get_servers(self, lobby_id: IntValue) -> List[dict]:
        if not self.completed_step(TheaterStep.user):
            await self.authenticate()

        async with self.transaction() as tid:
            server_list_packet = self.build_glst_packet(tid, str(lobby_id).encode(ENCODING))
            await self.connection.write(server_list_packet)

            # Again, same procedure: Theater first responds with a GLST packet which indicates the number of games/servers
            # in the lobby. It then sends one GDAT packet per game/server
            glst_response = await self.wrapped_read(tid)
            # Response may indicate an error if given lobby id does not exist
            is_error, error = self.is_error_response(glst_response)
            if is_error:
                raise error
            glst = glst_response.get_payload()

            # GLST contains LOBBY-NUM-GAMES (total number of games in lobby) and
            # NUM-GAMES (number of games matching filters), so NUM-GAMES <= LOBBY-NUM-GAMES,
            # => Use NUM-GAMES since Theater will only return GDAT packet for servers matching the filters
            num_games = glst.get_int('NUM-GAMES', int())

            # Retrieve GDAT for all servers
            servers = []
            for i in range(num_games):
                gdat_response = await self.wrapped_read(tid)
                gdat = gdat_response.get_payload(TheaterParseMap.GDAT)
                servers.append(dict(gdat))

            return servers

    async def get_server_details(self, lobby_id: IntValue, game_id: IntValue) -> Tuple[dict, dict, List[dict]]:
        return await self.get_gdat(LID=lobby_id, GID=game_id)

    async def get_current_server(self, user_id: IntValue) -> Tuple[dict, dict, List[dict]]:
        return await self.get_gdat(UID=user_id)

    async def get_gdat(self, **kwargs: IntValue) -> Tuple[dict, dict, List[dict]]:
        if not self.completed_step(TheaterStep.user):
            await self.authenticate()

        async with self.transaction() as tid:
            server_details_packet = self.build_gdat_packet(
                tid,
                **kwargs
            )
            await self.connection.write(server_details_packet)

            # Similar structure to before, but with one difference: Theater returns a GDAT packet (general game data),
            # followed by a GDET packet (extended server data). Finally, it sends a PDAT packet for every player
            gdat_response = await self.wrapped_read(tid)
            # Response may indicate an error if given lobby id and /or game id do not exist
            is_error, error = self.is_error_response(gdat_response)
            if is_error:
                raise error
            gdat = gdat_response.get_payload(TheaterParseMap.GDAT)
            gdet_response = await self.wrapped_read(tid)
            gdet = gdet_response.get_payload(TheaterParseMap.GDET)

            # Determine number of active players (AP)
            num_players = gdat.get_int('AP', int())
            # Read PDAT packets for all players
            players = []
            for i in range(num_players):
                pdat_response = await self.wrapped_read(tid)
                pdat = pdat_response.get_payload(TheaterParseMap.PDAT)
                players.append(dict(pdat))

            return dict(gdat), dict(gdet), players
