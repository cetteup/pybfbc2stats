from typing import List, Tuple, Optional, Dict

from .asyncio_connection import AsyncSecureConnection, AsyncConnection
from .client import Client, FeslClient, TheaterClient
from .constants import FeslStep, Namespace, BACKEND_DETAILS, Platform, LookupType, DEFAULT_LEADERBOARD_KEYS, STATS_KEYS, \
    TheaterStep
from .exceptions import PyBfbc2StatsNotFoundError, PyBfbc2StatsAuthError
from .packet import Packet


class AsyncClient(Client):
    connection: AsyncConnection

    def __init__(self, connection: AsyncConnection, platform: Platform, timeout: float = 3.0, track_steps: bool = True):
        super().__init__(connection, platform, timeout, track_steps)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self.connection.close()


class AsyncFeslClient(AsyncClient):
    username: bytes
    password: bytes
    connection: AsyncSecureConnection
    completed_steps: Dict[FeslStep, Packet]

    def __init__(self, username: str, password: str, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        connection = AsyncSecureConnection(
            BACKEND_DETAILS[platform]['host'],
            BACKEND_DETAILS[platform]['port'],
            timeout
        )
        super().__init__(connection, platform, timeout, track_steps)
        self.username = username.encode('utf8')
        self.password = password.encode('utf8')

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self.logout()
        await self.connection.close()

    async def hello(self) -> bytes:
        if self.track_steps and FeslStep.hello in self.completed_steps:
            return bytes(self.completed_steps[FeslStep.hello])

        hello_packet = FeslClient.build_hello_packet(BACKEND_DETAILS[self.platform]['clientString'])
        await self.connection.write(hello_packet)

        # FESL sends hello response immediately followed initial memcheck => read both and return hello response
        response = await self.connection.read()
        _ = await self.connection.read()

        self.completed_steps[FeslStep.hello] = response

        # Reply to initial memcheck
        await self.memcheck()

        return bytes(response)

    async def memcheck(self) -> None:
        memcheck_packet = FeslClient.build_memcheck_packet()
        await self.connection.write(memcheck_packet)

    async def login(self) -> bytes:
        if self.track_steps and FeslStep.login in self.completed_steps:
            return bytes(self.completed_steps[FeslStep.login])
        elif self.track_steps and FeslStep.hello not in self.completed_steps:
            await self.hello()

        login_packet = FeslClient.build_login_packet(self.username, self.password)
        await self.connection.write(login_packet)
        response = await self.connection.read()

        response_valid, error_message = FeslClient.is_valid_login_response(response)
        if not response_valid:
            raise PyBfbc2StatsAuthError(error_message)

        self.completed_steps[FeslStep.login] = response

        return bytes(response)

    async def logout(self) -> Optional[bytes]:
        # Only send logout if client is currently logged in
        if self.track_steps and FeslStep.login in self.completed_steps:
            logout_packet = FeslClient.build_logout_packet()
            await self.connection.write(logout_packet)
            self.completed_steps.clear()
            return bytes(await self.connection.read())

    async def ping(self) -> None:
        ping_packet = FeslClient.build_ping_packet()
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

    async def lookup_user_ids(self, user_ids: List[int], namespace: Namespace) -> List[dict]:
        user_ids_str = [str(user_id) for user_id in user_ids]
        return await self.lookup_user_identifiers(user_ids_str, namespace, LookupType.byId)

    async def lookup_user_id(self, user_id: int, namespace: Namespace) -> dict:
        return await self.lookup_user_identifier(str(user_id), namespace, LookupType.byId)

    async def lookup_user_identifiers(self, identifiers: List[str], namespace: Namespace,
                                      lookup_type: LookupType) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        lookup_packet = FeslClient.build_user_lookup_packet(identifiers, namespace, lookup_type)
        await self.connection.write(lookup_packet)

        parsed_response, *_ = await self.get_list_response(b'userInfo.')
        return parsed_response

    async def lookup_user_identifier(self, identifier: str, namespace: Namespace, lookup_type: LookupType) -> dict:
        results = await self.lookup_user_identifiers([identifier], namespace, lookup_type)

        if len(results) == 0:
            raise PyBfbc2StatsNotFoundError('User lookup did not return any results')

        return results.pop()

    async def search_name(self, screen_name: str, namespace: Namespace) -> dict:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        search_packet = FeslClient.build_search_packet(screen_name, namespace)
        await self.connection.write(search_packet)

        parsed_response, metadata = await self.get_list_response(b'users.')
        return FeslClient.format_search_response(parsed_response, metadata)

    async def get_stats(self, userid: int, keys: List[bytes] = STATS_KEYS) -> dict:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        # Send query in chunks
        chunk_packets = FeslClient.build_stats_query_packets(userid, keys)
        for chunk_packet in chunk_packets:
            await self.connection.write(chunk_packet)

        parsed_response, *_ = await self.get_list_response(b'stats.')
        return self.dict_list_to_dict(parsed_response)

    async def get_leaderboard(self, min_rank: int = 1, max_rank: int = 50, sort_by: bytes = b'score',
                              keys: List[bytes] = DEFAULT_LEADERBOARD_KEYS) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            await self.login()

        leaderboard_packet = FeslClient.build_leaderboard_query_packet(min_rank, max_rank, sort_by, keys)
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
                data, last_packet = FeslClient.handle_list_response_packet(packet, list_entry_prefix)
                response += data

        return FeslClient.parse_list_response(response, list_entry_prefix)


class AsyncTheaterClient(AsyncClient):
    lkey: bytes
    transaction_id: int = 0
    completed_steps: Dict[TheaterStep, Packet]

    def __init__(self, host: str, port: int, lkey: str, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        connection = AsyncConnection(host, port)
        super().__init__(connection, platform, timeout, track_steps)
        self.lkey = lkey.encode('utf8')

    async def connect(self) -> bytes:
        """
        Initialize the connection to the Theater backend by sending the initial CONN/hello packet
        :return: Response packet data
        """
        if self.track_steps and TheaterStep.conn in self.completed_steps:
            return bytes(self.completed_steps[TheaterStep.conn])

        tid = self.get_transaction_id()
        connect_packet = TheaterClient.build_conn_paket(tid, BACKEND_DETAILS[self.platform]['clientString'])
        await self.connection.write(connect_packet)

        response = await self.connection.read()
        self.completed_steps[TheaterStep.conn] = response

        return bytes(response)

    async def authenticate(self) -> bytes:
        """
        Authenticate against/log into the Theater backend using the lkey retrieved via FESL
        :return: Response packet data
        """
        if self.track_steps and TheaterStep.user in self.completed_steps:
            return bytes(self.completed_steps[TheaterStep.user])
        elif self.track_steps and TheaterStep.conn not in self.completed_steps:
            await self.connect()

        tid = self.get_transaction_id()
        auth_packet = TheaterClient.build_user_packet(tid, self.lkey)
        await self.connection.write(auth_packet)

        response = await self.connection.read()

        if not TheaterClient.is_valid_authentication_response(response):
            raise PyBfbc2StatsAuthError('Theater authentication failed')

        self.completed_steps[TheaterStep.user] = response

        return bytes(response)

    async def get_lobbies(self) -> List[dict]:
        """
        Retrieve all available game (server) lobbies
        :return: List of lobby details
        """
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            await self.authenticate()

        tid = self.get_transaction_id()
        lobby_list_packet = TheaterClient.build_llst_packet(tid)
        await self.connection.write(lobby_list_packet)

        # Theater responds with an initial LLST packet, indicating the number of lobbies,
        # followed by n LDAT packets with the lobby details
        llst_response = await self.connection.read()
        llst = self.parse_simple_response(llst_response)
        num_lobbies = int(llst['NUM-LOBBIES'])

        # Retrieve given number of lobbies (usually just one these days)
        lobbies = []
        for i in range(num_lobbies):
            ldat_response = await self.connection.read()
            ldat = self.parse_simple_response(ldat_response)
            lobbies.append(ldat)

        return lobbies

    async def get_servers(self, lobby_id: int) -> List[dict]:
        """
        Retrieve all available game servers from the given lobby
        :param lobby_id: Id of the game server lobby
        :return: List of server details
        """
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            await self.authenticate()

        tid = self.get_transaction_id()
        server_list_packet = TheaterClient.build_glst_packet(tid, str(lobby_id).encode('utf8'))
        await self.connection.write(server_list_packet)

        # Again, same procedure: Theater first responds with a GLST packet which indicates the number of games/servers
        # in the lobby. It then sends one GDAT packet per game/server
        glst_response = await self.connection.read()
        glst = self.parse_simple_response(glst_response)
        num_games = int(glst['LOBBY-NUM-GAMES'])

        # Retrieve GDAT for all servers
        servers = []
        for i in range(num_games):
            gdat_response = await self.connection.read()
            gdat = self.parse_simple_response(gdat_response)
            servers.append(gdat)

        return servers

    async def get_server_details(self, lobby_id: int, game_id: int) -> Tuple[dict, dict, List[dict]]:
        """
        Retrieve full details and player list for a given server
        :param lobby_id: If of the game server lobby the server is hosted in
        :param game_id: Game (server) id
        :return: Tuple of (general server details, extended details, player list)
        """
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            await self.authenticate()

        tid = self.get_transaction_id()
        server_details_packet = TheaterClient.build_gdat_packet(
            tid,
            str(lobby_id).encode('utf8'),
            str(game_id).encode('utf8')
        )
        await self.connection.write(server_details_packet)

        # Similar structure to before, but with one difference: Theater returns a GDAT packet (general game data),
        # followed by a GDET packet (extended server data). Finally, it sends a PDAT packet for every player
        gdat_response = await self.connection.read()
        gdat = self.parse_simple_response(gdat_response)
        gdet_response = await self.connection.read()
        gdet = self.parse_simple_response(gdet_response)

        # Determine number of active players (AP)
        num_players = int(gdat['AP'])
        # Read PDAT packets for all players
        players = []
        for i in range(num_players):
            pdat_response = await self.connection.read()
            pdat = self.parse_simple_response(pdat_response)
            players.append(pdat)

        return gdat, gdet, players

    def get_transaction_id(self) -> bytes:
        """
        "Assign" a transaction id (each packet sent to Theater must have a sequential tid/transaction id)
        :return: Transaction id as bytes
        """
        self.transaction_id += 1
        return str(self.transaction_id).encode('utf8')
