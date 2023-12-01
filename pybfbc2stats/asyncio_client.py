from typing import List, Tuple, Optional, Union

from .asyncio_connection import AsyncSecureConnection, AsyncConnection
from .client import Client, FeslClient, TheaterClient
from .constants import FeslStep, Namespace, BACKEND_DETAILS, Platform, LookupType, DEFAULT_LEADERBOARD_KEYS, STATS_KEYS, \
    TheaterStep, ENCODING, FeslParseMap, TheaterParseMap
from .exceptions import PlayerNotFoundError, AuthError, ConnectionError, TimeoutError
from .packet import Packet, FeslPacket, TheaterPacket
from .payload import Payload, StrValue, IntValue, ParseMap


class AsyncClient(Client):
    connection: AsyncConnection

    def __init__(
            self,
            connection: AsyncConnection,
            platform: Platform,
            client_string: StrValue,
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

    def __init__(self, username: StrValue, password: StrValue, platform: Platform, timeout: float = 3.0,
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
        self.username = username
        self.password = password

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

        response_valid, error_message, code = self.is_valid_login_response(response)
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
        payload = packet.get_payload()

        # Field is called "ip" but actually contains the hostname
        return payload.get_str('theaterIp', str()), payload.get_int('theaterPort', int())

    async def get_lkey(self) -> str:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        packet = self.completed_steps[FeslStep.login]
        payload = packet.get_payload()

        return payload.get_str('lkey', str())

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
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        tid = self.get_transaction_id()
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
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        tid = self.get_transaction_id()
        search_packet = self.build_search_packet(tid, screen_name, namespace)
        await self.connection.write(search_packet)

        payload = await self.get_response(tid, parse_map=FeslParseMap.NameSearch)
        return {
            'namespace': payload.get_str('nameSpaceId', str()),
            'users': payload.get_list('users', list())
        }

    async def get_stats(self, userid: IntValue, keys: List[StrValue] = STATS_KEYS) -> dict:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        # Send query in chunks (using the same transaction id for all packets)
        tid = self.get_transaction_id()
        chunk_packets = self.build_stats_query_packets(tid, userid, keys)
        for chunk_packet in chunk_packets:
            await self.connection.write(chunk_packet)

        payload = await self.get_response(tid, parse_map=FeslParseMap.Stats)
        return self.dict_list_to_dict(payload.get_list('stats', list()))

    async def get_leaderboard(self, min_rank: IntValue = 1, max_rank: IntValue = 50, sort_by: StrValue = 'score',
                              keys: List[StrValue] = DEFAULT_LEADERBOARD_KEYS) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        tid = self.get_transaction_id()
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
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        tid = self.get_transaction_id()
        dogtags_packet = self.build_dogtag_query_packet(tid, userid)
        await self.connection.write(dogtags_packet)

        payload = await self.get_response(tid)
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
        # "Skip" TheaterClient constructor, for details see note in AsyncFeslClient.__init__
        super(TheaterClient, self).__init__(
            connection,
            platform,
            BACKEND_DETAILS[platform]['clientString'],
            timeout,
            track_steps
        )
        self.lkey = lkey

    async def connect(self) -> bytes:
        if self.track_steps and TheaterStep.conn in self.completed_steps:
            return bytes(self.completed_steps[TheaterStep.conn])

        tid = self.get_transaction_id()
        connect_packet = self.build_conn_packet(tid, self.client_string)
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
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            await self.authenticate()

        tid = self.get_transaction_id()
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
