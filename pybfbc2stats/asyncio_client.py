from typing import List, Tuple, Optional, Union

from .asyncio_connection import AsyncSecureConnection, AsyncConnection
from .client import Client, FeslClient, TheaterClient
from .constants import FeslStep, Namespace, BACKEND_DETAILS, Platform, LookupType, DEFAULT_LEADERBOARD_KEYS, STATS_KEYS, \
    TheaterStep
from .exceptions import PlayerNotFoundError, AuthError, ConnectionError, TimeoutError
from .packet import Packet, FeslPacket, TheaterPacket


class AsyncClient(Client):
    connection: AsyncConnection

    def __init__(
            self,
            connection: AsyncConnection,
            platform: Platform,
            client_string: bytes,
            timeout: float = 3.0,
            track_steps: bool = True
    ):
        super().__init__(connection, platform, client_string, timeout, track_steps)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self.connection.close()

    async def wrapped_read(self, tid: int) -> Packet:
        initial_packet = await self.connection.read()

        # Check packet is not a "real" data packet but one that prompts a response (memcheck, ping)
        auto_respond, handler = self.is_auto_respond_packet(initial_packet)
        if auto_respond:
            # Call auto respond handler
            await handler()
            # Call self to read another packet
            data_packet = await self.wrapped_read(tid)
        elif initial_packet.get_tid() < tid:
            # Call self to read another packet if packet is not part of current transaction
            data_packet = await self.wrapped_read(tid)
        else:
            data_packet = initial_packet

        return data_packet


class AsyncFeslClient(FeslClient, AsyncClient):
    connection: AsyncSecureConnection

    def __init__(self, username: str, password: str, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        connection = AsyncSecureConnection(
            BACKEND_DETAILS[platform]['host'],
            BACKEND_DETAILS[platform]['port'],
            FeslPacket,
            timeout
        )
        """
        Multiple inheritance works here, but only if we "skip" the FeslClient constructor. The method resolution here
        is: AsyncFeslClient, FeslClient, AsyncClient, Client. So, by calling super(), we would call the FeslClient
        __init__ function with parameters that make no sense. If we instead use super(FeslClient, self), we call
        FeslClient's super directly - effectively skipping the FeslClient constructor
        """
        super(FeslClient, self).__init__(
            connection,
            platform,
            BACKEND_DETAILS[platform]['clientString'],
            timeout,
            track_steps
        )
        self.username = username.encode('utf8')
        self.password = password.encode('utf8')

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        try:
            await self.logout()
        except (ConnectionError, TimeoutError):
            pass
        await self.connection.close()

    async def hello(self) -> bytes:
        if self.track_steps and FeslStep.hello in self.completed_steps:
            return bytes(self.completed_steps[FeslStep.hello])

        tid = self.get_transaction_id()
        hello_packet = self.build_hello_packet(tid, self.client_string)
        await self.connection.write(hello_packet)

        # FESL sends hello response immediately followed initial memcheck => read both and return hello response
        response = await self.connection.read()
        _ = await self.connection.read()

        self.completed_steps[FeslStep.hello] = response

        # Reply to initial memcheck
        await self.memcheck()

        return bytes(response)

    async def memcheck(self) -> None:
        memcheck_packet = self.build_memcheck_packet()
        await self.connection.write(memcheck_packet)

    async def login(self) -> bytes:
        if self.track_steps and FeslStep.login in self.completed_steps:
            return bytes(self.completed_steps[FeslStep.login])
        elif self.track_steps and FeslStep.hello not in self.completed_steps:
            await self.hello()

        tid = self.get_transaction_id()
        login_packet = self.build_login_packet(tid, self.username, self.password)
        await self.connection.write(login_packet)
        response = await self.wrapped_read(tid)

        response_valid, error_message = self.is_valid_login_response(response)
        if not response_valid:
            raise AuthError(error_message)

        self.completed_steps[FeslStep.login] = response

        return bytes(response)

    async def logout(self) -> Optional[bytes]:
        # Only send logout if client is currently logged in
        if self.track_steps and FeslStep.login in self.completed_steps:
            tid = self.get_transaction_id()
            logout_packet = self.build_logout_packet(tid)
            await self.connection.write(logout_packet)
            self.completed_steps.clear()
            return bytes(await self.wrapped_read(tid))

    async def ping(self) -> None:
        ping_packet = self.build_ping_packet()
        await self.connection.write(ping_packet)

    async def get_theater_details(self) -> Tuple[str, int]:
        if self.track_steps and FeslStep.hello not in self.completed_steps:
            await self.hello()

        packet = self.completed_steps[FeslStep.hello]
        parsed = self.parse_simple_response(packet)

        # Field is called "ip" but actually contains the hostname
        return parsed['theaterIp'], int(parsed['theaterPort'])

    async def get_lkey(self) -> str:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        packet = self.completed_steps[FeslStep.login]
        parsed = self.parse_simple_response(packet)

        return parsed['lkey']

    async def lookup_usernames(self, usernames: List[str], namespace: Namespace) -> List[dict]:
        return await self.lookup_user_identifiers(usernames, namespace, LookupType.byName)

    async def lookup_username(self, username: str, namespace: Namespace) -> dict:
        return await self.lookup_user_identifier(username, namespace, LookupType.byName)

    async def lookup_user_ids(self, user_ids: List[Union[int, str]], namespace: Namespace) -> List[dict]:
        return await self.lookup_user_identifiers(user_ids, namespace, LookupType.byId)

    async def lookup_user_id(self, user_id: Union[int, str], namespace: Namespace) -> dict:
        return await self.lookup_user_identifier(user_id, namespace, LookupType.byId)

    async def lookup_user_identifiers(self, identifiers: List[Union[str, int]], namespace: Namespace,
                                      lookup_type: LookupType) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        tid = self.get_transaction_id()
        lookup_packet = self.build_user_lookup_packet(tid, identifiers, namespace, lookup_type)
        await self.connection.write(lookup_packet)

        raw_response = await self.get_complex_response(tid)
        parsed_response, *_ = self.parse_list_response(raw_response, b'userInfo.')
        return parsed_response

    async def lookup_user_identifier(self, identifier: Union[str, int], namespace: Namespace, lookup_type: LookupType) -> dict:
        results = await self.lookup_user_identifiers([identifier], namespace, lookup_type)

        if len(results) == 0:
            raise PlayerNotFoundError('User lookup did not return any results')

        return results.pop()

    async def search_name(self, screen_name: str, namespace: Namespace) -> dict:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        tid = self.get_transaction_id()
        search_packet = self.build_search_packet(tid, screen_name, namespace)
        await self.connection.write(search_packet)

        raw_response = await self.get_complex_response(tid)
        parsed_response, metadata = self.parse_list_response(raw_response, b'users.')
        return self.format_search_response(parsed_response, metadata)

    async def get_stats(self, userid: Union[int, str], keys: List[bytes] = STATS_KEYS) -> dict:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        # Send query in chunks (using the same transaction id for all packets)
        tid = self.get_transaction_id()
        chunk_packets = self.build_stats_query_packets(tid, userid, keys)
        for chunk_packet in chunk_packets:
            await self.connection.write(chunk_packet)

        raw_response = await self.get_complex_response(tid)
        parsed_response, *_ = self.parse_list_response(raw_response, b'stats.')
        return self.dict_list_to_dict(parsed_response)

    async def get_leaderboard(self, min_rank: int = 1, max_rank: int = 50, sort_by: bytes = b'score',
                              keys: List[bytes] = DEFAULT_LEADERBOARD_KEYS) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        tid = self.get_transaction_id()
        leaderboard_packet = self.build_leaderboard_query_packet(tid, min_rank, max_rank, sort_by, keys)
        await self.connection.write(leaderboard_packet)

        raw_response = await self.get_complex_response(tid)
        parsed_response, *_ = self.parse_list_response(raw_response, b'stats.')
        # Turn sub lists into dicts and return result
        return [{key: Client.dict_list_to_dict(value) if isinstance(value, list) else value
                 for (key, value) in persona.items()} for persona in parsed_response]

    async def get_dogtags(self, userid: Union[int, str]) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        tid = self.get_transaction_id()
        dogtags_packet = self.build_dogtag_query_packet(tid, userid)
        await self.connection.write(dogtags_packet)

        raw_response = await self.get_complex_response(tid)
        parsed_response, *_ = self.parse_map_response(raw_response, b'values.')
        return self.format_dogtags_response(parsed_response, self.platform)

    async def get_complex_response(self, tid: int) -> bytes:
        response = b''
        last_packet = False
        while not last_packet:
            packet = await self.wrapped_read(tid)
            data, last_packet = self.process_complex_response_packet(packet)
            response += data

        return response


class AsyncTheaterClient(TheaterClient, AsyncClient):
    def __init__(self, host: str, port: int, lkey: str, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        connection = AsyncConnection(host, port, TheaterPacket)
        # "Skip" TheaterClient constructor, for details see note in AsyncFeslClient.__init__
        super(TheaterClient, self).__init__(
            connection,
            platform,
            BACKEND_DETAILS[platform]['clientString'],
            timeout,
            track_steps
        )
        self.lkey = lkey.encode('utf8')

    async def connect(self) -> bytes:
        if self.track_steps and TheaterStep.conn in self.completed_steps:
            return bytes(self.completed_steps[TheaterStep.conn])

        tid = self.get_transaction_id()
        connect_packet = self.build_conn_paket(tid, self.client_string)
        await self.connection.write(connect_packet)

        response = await self.connection.read()
        self.completed_steps[TheaterStep.conn] = response

        return bytes(response)

    async def authenticate(self) -> bytes:
        if self.track_steps and TheaterStep.user in self.completed_steps:
            return bytes(self.completed_steps[TheaterStep.user])
        elif self.track_steps and TheaterStep.conn not in self.completed_steps:
            await self.connect()

        tid = self.get_transaction_id()
        auth_packet = self.build_user_packet(tid, self.lkey)
        await self.connection.write(auth_packet)

        response = await self.connection.read()

        if not self.is_valid_authentication_response(response):
            raise AuthError('Theater authentication failed')

        self.completed_steps[TheaterStep.user] = response

        return bytes(response)

    async def ping(self) -> None:
        ping_packet = self.build_ping_packet()
        await self.connection.write(ping_packet)

    async def get_lobbies(self) -> List[dict]:
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            await self.authenticate()

        tid = self.get_transaction_id()
        lobby_list_packet = self.build_llst_packet(tid)
        await self.connection.write(lobby_list_packet)

        # Theater responds with an initial LLST packet, indicating the number of lobbies,
        # followed by n LDAT packets with the lobby details
        llst_response = await self.wrapped_read(tid)
        llst = self.parse_simple_response(llst_response)
        num_lobbies = int(llst['NUM-LOBBIES'])

        # Retrieve given number of lobbies (usually just one these days)
        lobbies = []
        for i in range(num_lobbies):
            ldat_response = await self.wrapped_read(tid)
            ldat = self.parse_simple_response(ldat_response)
            lobbies.append(ldat)

        return lobbies

    async def get_servers(self, lobby_id: Union[int, str]) -> List[dict]:
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            await self.authenticate()

        tid = self.get_transaction_id()
        server_list_packet = self.build_glst_packet(tid, str(lobby_id).encode('utf8'))
        await self.connection.write(server_list_packet)

        # Again, same procedure: Theater first responds with a GLST packet which indicates the number of games/servers
        # in the lobby. It then sends one GDAT packet per game/server
        glst_response = await self.wrapped_read(tid)
        # Response may indicate an error if given lobby id does not exist
        is_error, error = self.is_error_response(glst_response)
        if is_error:
            raise error
        glst = self.parse_simple_response(glst_response)

        # GLST contains LOBBY-NUM-GAMES (total number of games in lobby) and
        # NUM-GAMES (number of games matching filters), so NUM-GAMES <= LOBBY-NUM-GAMES,
        # => Use NUM-GAMES since Theater will only return GDAT packet for servers matching the filters
        num_games = int(glst['NUM-GAMES'])

        # Retrieve GDAT for all servers
        servers = []
        for i in range(num_games):
            gdat_response = await self.wrapped_read(tid)
            gdat = self.parse_simple_response(gdat_response)
            servers.append(gdat)

        return servers

    async def get_server_details(self, lobby_id: Union[int, str], game_id: Union[int, str]) -> Tuple[dict, dict, List[dict]]:
        return await self.get_gdat(lid=str(lobby_id).encode('utf8'), gid=str(game_id).encode('utf8'))

    async def get_current_server(self, user_id: Union[int, str]) -> Tuple[dict, dict, List[dict]]:
        return await self.get_gdat(uid=str(user_id).encode('utf8'))

    async def get_gdat(self, **kwargs: bytes) -> Tuple[dict, dict, List[dict]]:
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            await self.authenticate()

        tid = self.get_transaction_id()
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
        gdat = self.parse_simple_response(gdat_response)
        gdet_response = await self.wrapped_read(tid)
        gdet = self.parse_simple_response(gdet_response)

        # Determine number of active players (AP)
        num_players = int(gdat['AP'])
        # Read PDAT packets for all players
        players = []
        for i in range(num_players):
            pdat_response = await self.wrapped_read(tid)
            pdat = self.parse_simple_response(pdat_response)
            players.append(pdat)

        return gdat, gdet, players
