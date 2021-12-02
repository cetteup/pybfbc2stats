from base64 import b64encode, b64decode
from typing import List, Union, Dict, Tuple, Optional
from urllib.parse import quote_from_bytes, unquote_to_bytes

from .connection import SecureConnection, Connection
from .constants import STATS_KEYS, DEFAULT_BUFFER_SIZE, FeslStep, Namespace, Platform, BACKEND_DETAILS, LookupType, \
    DEFAULT_LEADERBOARD_KEYS, Step, TheaterStep
from .exceptions import PyBfbc2StatsParameterError, PyBfbc2StatsError, PyBfbc2StatsNotFoundError, \
    PyBfbc2StatsSearchError, PyBfbc2StatsAuthError
from .packet import Packet


class Client:
    platform: Platform
    timeout: float
    track_steps: bool
    connection: Connection
    completed_steps: Dict[Step, Packet]

    def __init__(self, connection: Connection, platform: Platform, timeout: float = 3.0, track_steps: bool = True):
        self.platform = platform
        self.track_steps = track_steps
        self.connection = connection
        # Using the client with too short of a timeout leads to lots if issues with reads timing out and subsequent
        # reads then reading data from the previous "request" => enforce minimum timeout of 2 seconds
        self.connection.timeout = max(timeout, 2.0)
        self.completed_steps = {}

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        self.connection.close()

    @staticmethod
    def parse_simple_response(packet: Packet) -> dict:
        parsed = {}
        for line in packet.get_data_lines():
            elements = line.split(b'=', 1)
            if len(elements) == 2:
                key = elements[0].decode()
                value = elements[1].decode()
                parsed[key] = value

        return parsed

    @staticmethod
    def dict_list_to_dict(dict_list: List[dict]) -> dict:
        sorted_list = sorted(dict_list, key=lambda x: x['key'])
        return {entry['key']: entry['value'] for entry in sorted_list}


class FeslClient(Client):
    username: bytes
    password: bytes
    connection: SecureConnection
    completed_steps: Dict[FeslStep, Packet]

    def __init__(self, username: str, password: str, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        connection = SecureConnection(
            BACKEND_DETAILS[platform]['host'],
            BACKEND_DETAILS[platform]['port']
        )
        super().__init__(connection, platform, timeout, track_steps)
        self.username = username.encode('utf8')
        self.password = password.encode('utf8')

    def __exit__(self, *excinfo):
        self.logout()
        self.connection.close()

    def hello(self) -> bytes:
        if self.track_steps and FeslStep.hello in self.completed_steps:
            return bytes(self.completed_steps[FeslStep.hello])

        hello_packet = self.build_hello_packet(BACKEND_DETAILS[self.platform]['clientString'])
        self.connection.write(hello_packet)

        # FESL sends hello response immediately followed initial memcheck => read both and return hello response
        response = self.connection.read()
        _ = self.connection.read()

        self.completed_steps[FeslStep.hello] = response

        # Reply to initial memcheck
        self.memcheck()

        return bytes(response)

    def memcheck(self) -> None:
        memcheck_packet = self.build_memcheck_packet()
        self.connection.write(memcheck_packet)

    def login(self) -> bytes:
        if self.track_steps and FeslStep.login in self.completed_steps:
            return bytes(self.completed_steps[FeslStep.login])
        elif self.track_steps and FeslStep.hello not in self.completed_steps:
            self.hello()

        login_packet = self.build_login_packet(self.username, self.password)
        self.connection.write(login_packet)
        response = self.connection.read()

        response_valid, error_message = self.is_valid_login_response(response)
        if not response_valid:
            raise PyBfbc2StatsAuthError(error_message)

        self.completed_steps[FeslStep.login] = response

        return bytes(response)

    def logout(self) -> Optional[bytes]:
        if self.track_steps and FeslStep.login in self.completed_steps:
            logout_packet = self.build_logout_packet()
            self.connection.write(logout_packet)
            self.completed_steps.clear()
            return bytes(self.connection.read())

    def ping(self) -> None:
        ping_packet = self.build_ping_packet()
        self.connection.write(ping_packet)

    def get_theater_details(self) -> Tuple[str, int]:
        if self.track_steps and FeslStep.hello not in self.completed_steps:
            self.hello()

        packet = self.completed_steps[FeslStep.hello]
        parsed = self.parse_simple_response(packet)

        # Field is called "ip" but actually contains the hostname
        return parsed['theaterIp'], int(parsed['theaterPort'])

    def get_lkey(self) -> str:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        packet = self.completed_steps[FeslStep.login]
        parsed = self.parse_simple_response(packet)

        return parsed['lkey']

    def lookup_usernames(self, usernames: List[str], namespace: Namespace) -> List[dict]:
        return self.lookup_user_identifiers(usernames, namespace, LookupType.byName)

    def lookup_username(self, username: str, namespace: Namespace) -> dict:
        return self.lookup_user_identifier(username, namespace, LookupType.byName)

    def lookup_user_ids(self, user_ids: List[int], namespace: Namespace) -> List[dict]:
        user_ids_str = [str(user_id) for user_id in user_ids]
        return self.lookup_user_identifiers(user_ids_str, namespace, LookupType.byId)

    def lookup_user_id(self, user_id: int, namespace: Namespace) -> dict:
        return self.lookup_user_identifier(str(user_id), namespace, LookupType.byId)

    def lookup_user_identifiers(self, identifiers: List[str], namespace: Namespace,
                                lookup_type: LookupType) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        lookup_packet = self.build_user_lookup_packet(identifiers, namespace, lookup_type)
        self.connection.write(lookup_packet)

        parsed_response, *_ = self.get_list_response(b'userInfo.')
        return parsed_response

    def lookup_user_identifier(self, identifier: str, namespace: Namespace, lookup_type: LookupType) -> dict:
        results = self.lookup_user_identifiers([identifier], namespace, lookup_type)

        if len(results) == 0:
            raise PyBfbc2StatsNotFoundError('User lookup did not return any results')

        return results.pop()

    def search_name(self, screen_name: str, namespace: Namespace) -> dict:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        search_packet = self.build_search_packet(screen_name, namespace)
        self.connection.write(search_packet)

        parsed_response, metadata = self.get_list_response(b'users.')
        return self.format_search_response(parsed_response, metadata)

    def get_stats(self, userid: int, keys: List[bytes] = STATS_KEYS) -> dict:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        # Send query in chunks
        chunk_packets = self.build_stats_query_packets(userid, keys)
        for chunk_packet in chunk_packets:
            self.connection.write(chunk_packet)

        parsed_response, *_ = self.get_list_response(b'stats.')
        return self.dict_list_to_dict(parsed_response)

    def get_leaderboard(self, min_rank: int = 1, max_rank: int = 50, sort_by: bytes = b'score',
                        keys: List[bytes] = DEFAULT_LEADERBOARD_KEYS) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        leaderboard_packet = self.build_leaderboard_query_packet(min_rank, max_rank, sort_by, keys)
        self.connection.write(leaderboard_packet)

        parsed_response, *_ = self.get_list_response(b'stats.')
        # Turn sub lists into dicts and return result
        return [{key: self.dict_list_to_dict(value) if isinstance(value, list) else value
                 for (key, value) in persona.items()} for persona in parsed_response]

    def get_list_response(self, list_entry_prefix: bytes) -> Tuple[List[dict], List[bytes]]:
        response = b''
        last_packet = False
        while not last_packet:
            packet = self.connection.read()
            if b'TXN=MemCheck' in packet.body:
                # Respond to memcheck
                self.memcheck()
            elif b'TXN=Ping' in packet.body:
                # Respond to ping
                self.ping()
            else:
                data, last_packet = self.handle_list_response_packet(packet, list_entry_prefix)
                response += data

        return self.parse_list_response(response, list_entry_prefix)

    @staticmethod
    def build_list_body(items: List[Union[bytes, Dict[bytes, bytes]]], prefix: bytes) -> bytes:
        # Convert item list to bytes following "prefix.index.key=value"-format
        item_list = []
        for index, item in enumerate(items):
            if isinstance(item, dict):
                for key, value in item.items():
                    dotted_elements = [prefix, str(index).encode('utf8'), key]
                    # byte dict with prefix: userInfo.0.userName=NoobKillah
                    item_list.append(FeslClient.build_list_item(dotted_elements, value))
            else:
                # bytes with prefix only: keys.0=accuracy
                dotted_elements = [prefix, str(index).encode('utf8')]
                item_list.append(FeslClient.build_list_item(dotted_elements, item))

        # Join list together, add list length indicator and return
        return b'\n'.join(item_list) + b'\n' + prefix + b'.[]=' + str(len(items)).encode('utf8')

    @staticmethod
    def build_list_item(dotted_elements: List[bytes], value: bytes) -> bytes:
        return b'.'.join(dotted_elements) + b'=' + value

    @staticmethod
    def build_hello_packet(client_string: bytes) -> Packet:
        return Packet.build(
            b'fsys\xc0\x00\x00\x01',
            b'TXN=Hello\nclientString=' + client_string +
            b'\nsku=PC\nlocale=en_US\nclientPlatform=PC\nclientVersion=2.0\nSDKVersion=5.1.2.0.0\nprotocolVersion=2.0\n'
            b'fragmentSize=8096\nclientType=server'
        )

    @staticmethod
    def build_memcheck_packet() -> Packet:
        return Packet.build(
            b'fsys\x80\x00\x00\x00',
            b'TXN=MemCheck\nresult='
        )

    @staticmethod
    def build_login_packet(username: bytes, password: bytes) -> Packet:
        return Packet.build(
            b'acct\xc0\x00\x00\x02',
            b'TXN=Login\nreturnEncryptedInfo=0\n'
            b'name=' + username + b'\npassword=' + password + b'\nmacAddr=$000000000000'
        )

    @staticmethod
    def build_logout_packet() -> Packet:
        return Packet.build(
            b'fsys\xc0\x00\x00\x03',
            b'TXN=Goodbye\nreason=GOODBYE_CLIENT_NORMAL\nmessage="Disconnected via front-end"'
        )

    @staticmethod
    def build_ping_packet() -> Packet:
        return Packet.build(
            b'fsys\x80\x00\x00\x00',
            b'TXN=Ping'
        )

    @staticmethod
    def build_user_lookup_packet(user_identifiers: List[str], namespace: Namespace, lookup_type: LookupType) -> Packet:
        user_dicts = [{bytes(lookup_type): identifier.encode('utf8'), b'namespace': bytes(namespace)}
                      for identifier in user_identifiers]
        lookup_list = FeslClient.build_list_body(user_dicts, b'userInfo')
        lookup_packet = Packet.build(
            b'acct\xc0\x00\x00\n',
            b'TXN=NuLookupUserInfo\n' + lookup_list
        )

        return lookup_packet

    @staticmethod
    def build_search_packet(screen_name: str, namespace: Namespace) -> Packet:
        return Packet.build(
            b'acct\xc0\x00\x00\x1c',
            b'TXN=NuSearchOwners\nscreenName=' + screen_name.encode('utf8') + b'\nsearchType=1\nretrieveUserIds=0\n'
            b'nameSpaceId=' + bytes(namespace)
        )

    @staticmethod
    def build_leaderboard_query_packet(min_rank: int, max_rank: int, sort_by: bytes, keys: List[bytes]) -> Packet:
        key_list = FeslClient.build_list_body(keys, b'keys')
        leaderboard_packet = Packet.build(
            b'rank\xc0\x00\x00\x00',
            b'TXN=GetTopNAndStats\nkey=' + sort_by + b'\nownerType=1\nminRank=' + str(min_rank).encode('utf8') +
            b'\nmaxRank=' + str(max_rank).encode('utf8') + b'\nperiodId=0\nperiodPast=0\nrankOrder=0\n' + key_list
        )

        return leaderboard_packet

    @staticmethod
    def build_stats_query_packets(userid: int, keys: List[bytes]) -> List[Packet]:
        userid_bytes = str(userid).encode('utf8')
        key_list = FeslClient.build_list_body(keys, b'keys')
        stats_query = b'TXN=GetStats\nowner=' + userid_bytes + b'\nownerType=1\nperiodId=0\nperiodPast=0\n' + key_list
        # Base64 encode query for transfer
        stats_query_b64 = b64encode(stats_query)
        # Determine available packet length (subtract already used by query metadata and size indicator)
        encoded_query_size = str(len(stats_query_b64))
        available_packet_length = DEFAULT_BUFFER_SIZE - (25 + len(encoded_query_size))

        # URL encode/quote query
        stats_query_enc = quote_from_bytes(stats_query_b64).encode('utf8')

        # Split query into chunks and build packets around them
        chunk_packets = []
        for i in range(0, len(stats_query_enc), available_packet_length):
            query_chunk = stats_query_enc[i:i + available_packet_length]
            chunk_packet = Packet.build(
                b'rank\xf0\x00\x00\x0b',
                b'size=' + encoded_query_size.encode('utf8') + b'\ndata=' + query_chunk
            )
            chunk_packets.append(chunk_packet)

        return chunk_packets

    @staticmethod
    def is_valid_login_response(response: Packet) -> Tuple[bool, str]:
        valid = b'lkey=' in response.body
        if not valid:
            lines = response.get_data_lines()
            message = next((line[18:-1] for line in lines if line.startswith(b'localizedMessage=')), b'').decode('utf8')
        else:
            message = ''

        return valid, message

    @staticmethod
    def parse_list_response(raw_response: bytes, list_entry_prefix: bytes) -> Tuple[List[dict], List[bytes]]:
        lines = raw_response.split(b'\n')
        # Assign lines to either data or meta lines
        meta_lines = []
        data_lines = []
        for line in lines:
            if line.startswith(list_entry_prefix) and list_entry_prefix + b'[]' not in line:
                # Append data line (without entry prefix)
                # So for userInfo.0.userId=226804555, only add 0.userId=226804555 (assuming prefix is userInfo.)
                data_lines.append(line[len(list_entry_prefix):])
            else:
                # Add meta data lines as is
                meta_lines.append(line)

        # Determine data entry count
        length_info = next(line for line in meta_lines if b'.[]' in line)
        entry_count = int(length_info.split(b'=').pop())
        # Init dict list
        datasets = [{} for _ in range(0, entry_count)]
        # Sort reverse to get sub-list length indicators first
        # (99.addStats.[]=10 will be sorted before 99.addStats.9.value=777.678)
        for line in sorted(data_lines, reverse=True):
            # Split into keys and data and split into index and key
            # line format will something like: 0.userId=22680455
            elements = line.split(b'=')
            key_elements = elements[0].split(b'.')
            index = int(key_elements[0])
            key = key_elements[1].decode()
            value = elements[1].decode()
            # Add sub-list (99.addStats.9.value=777.678) or simple scalar value (99.value=8.367105024E9)
            if len(key_elements) >= 3 and b'.[]=' in line:
                # If line contains a sub-list length indicator, init sub list of given length
                datasets[index][key] = [{} for _ in range(0, int(value))]
            elif len(key_elements) >= 4:
                # Line contains sub-list data => append to list at index and key
                sub_index = int(key_elements[2])
                sub_key = key_elements[3].decode()
                datasets[index][key][sub_index][sub_key] = value
            else:
                # Add scaler value to dict
                datasets[index][key] = value

        return datasets, meta_lines

    @staticmethod
    def handle_list_response_packet(packet: Packet, list_entry_prefix: bytes) -> Tuple[bytes, bool]:
        body = packet.get_data()
        lines = packet.get_data_lines()

        # Check for errors
        if b'errorCode' in body:
            method_line = next((line for line in lines if line.startswith(b'TXN')), b'')
            method = method_line.split(b'=').pop()
            error_code_line = next((line for line in lines if line.startswith(b'errorCode=')), b'')
            error_code = error_code_line.split(b'=').pop()
            if error_code == b'21':
                raise PyBfbc2StatsParameterError('FESL returned invalid parameter error')
            elif error_code == b'101' and method == b'NuLookupUserInfo':
                raise PyBfbc2StatsNotFoundError('FESL returned player not found error')
            elif error_code == b'104' and method == b'NuSearchOwners':
                # Error code is returned if a) no results matched the query or b) too many results matched the query
                raise PyBfbc2StatsSearchError('FESL found no or too many results matching the search query')
            else:
                raise PyBfbc2StatsError(f'FESL returned an error (code {error_code.decode("utf")})')
        elif b'data=' not in body and list_entry_prefix + b'[]' not in body:
            # Packet is neither one data packet of a multi-packet response nor a single-packet response
            raise PyBfbc2StatsError('FESL returned invalid response')

        if b'data=' in body:
            # Packet is one of multiple => base64 decode content
            data_line = next(line for line in lines if line.startswith(b'data='))
            # URL decode/unquote and base64 decode data
            data = b64decode(unquote_to_bytes(data_line[5:]))
            last_packet = data[-1:] == b'\x00'
            # Remove "eof" indicator from last packet's data
            if last_packet:
                data = data[:-1]
        else:
            # Single packet response => return body as is
            data = body
            last_packet = True

        return data, last_packet

    @staticmethod
    def format_search_response(parsed_response: List[dict], metadata: List[bytes]) -> dict:
        namespace_line = next(line for line in metadata if line.startswith(b'nameSpaceId'))
        namespace = namespace_line.split(b'=').pop()

        return {
            'namespace': namespace.decode('utf8'),
            'users': parsed_response
        }


class TheaterClient(Client):
    lkey: bytes
    transaction_id: int = 0
    completed_steps: Dict[TheaterStep, Packet]

    def __init__(self, host: str, port: int, lkey: str, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        connection = Connection(host, port)
        super().__init__(connection, platform, timeout, track_steps)
        self.lkey = lkey.encode('utf8')

    def connect(self) -> bytes:
        """
        Initialize the connection to the Theater backend by sending the initial CONN/hello packet
        :return: Response packet data
        """
        if self.track_steps and TheaterStep.conn in self.completed_steps:
            return bytes(self.completed_steps[TheaterStep.conn])

        tid = self.get_transaction_id()
        connect_packet = self.build_conn_paket(tid, BACKEND_DETAILS[self.platform]['clientString'])
        self.connection.write(connect_packet)

        response = self.connection.read()
        self.completed_steps[TheaterStep.conn] = response

        return bytes(response)

    def authenticate(self) -> bytes:
        """
        Authenticate against/log into the Theater backend using the lkey retrieved via FESL
        :return: Response packet data
        """
        if self.track_steps and TheaterStep.user in self.completed_steps:
            return bytes(self.completed_steps[TheaterStep.user])
        elif self.track_steps and TheaterStep.conn not in self.completed_steps:
            self.connect()

        tid = self.get_transaction_id()
        auth_packet = self.build_user_packet(tid, self.lkey)
        self.connection.write(auth_packet)

        response = self.connection.read()

        if not self.is_valid_authentication_response(response):
            raise PyBfbc2StatsAuthError('Theater authentication failed')

        self.completed_steps[TheaterStep.user] = response

        return bytes(response)

    def get_lobbies(self) -> List[dict]:
        """
        Retrieve all available game (server) lobbies
        :return: List of lobby details
        """
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            self.authenticate()

        tid = self.get_transaction_id()
        lobby_list_packet = self.build_llst_packet(tid)
        self.connection.write(lobby_list_packet)

        # Theater responds with an initial LLST packet, indicating the number of lobbies,
        # followed by n LDAT packets with the lobby details
        llst_response = self.connection.read()
        llst = self.parse_simple_response(llst_response)
        num_lobbies = int(llst['NUM-LOBBIES'])

        # Retrieve given number of lobbies (usually just one these days)
        lobbies = []
        for i in range(num_lobbies):
            ldat_response = self.connection.read()
            ldat = self.parse_simple_response(ldat_response)
            lobbies.append(ldat)

        return lobbies

    def get_servers(self, lobby_id: int) -> List[dict]:
        """
        Retrieve all available game servers from the given lobby
        :param lobby_id: Id of the game server lobby
        :return: List of server details
        """
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            self.authenticate()

        tid = self.get_transaction_id()
        server_list_packet = self.build_glst_packet(tid, str(lobby_id).encode('utf8'))
        self.connection.write(server_list_packet)

        # Again, same procedure: Theater first responds with a GLST packet which indicates the number of games/servers
        # in the lobby. It then sends one GDAT packet per game/server
        glst_response = self.connection.read()
        glst = self.parse_simple_response(glst_response)
        num_games = int(glst['LOBBY-NUM-GAMES'])

        # Retrieve GDAT for all servers
        servers = []
        for i in range(num_games):
            gdat_response = self.connection.read()
            gdat = self.parse_simple_response(gdat_response)
            servers.append(gdat)

        return servers

    def get_server_details(self, lobby_id: int, game_id: int) -> Tuple[dict, dict, List[dict]]:
        """
        Retrieve full details and player list for a given server
        :param lobby_id: If of the game server lobby the server is hosted in
        :param game_id: Game (server) id
        :return: Tuple of (general server details, extended details, player list)
        """
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            self.authenticate()

        tid = self.get_transaction_id()
        server_details_packet = self.build_gdat_packet(tid, str(lobby_id).encode('utf8'), str(game_id).encode('utf8'))
        self.connection.write(server_details_packet)

        # Similar structure to before, but with one difference: Theater returns a GDAT packet (general game data),
        # followed by a GDET packet (extended server data). Finally, it sends a PDAT packet for every player
        gdat_response = self.connection.read()
        gdat = self.parse_simple_response(gdat_response)
        gdet_response = self.connection.read()
        gdet = self.parse_simple_response(gdet_response)

        # Determine number of active players (AP)
        num_players = int(gdat['AP'])
        # Read PDAT packets for all players
        players = []
        for i in range(num_players):
            pdat_response = self.connection.read()
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

    @staticmethod
    def build_conn_paket(tid: bytes, client_string: bytes) -> Packet:
        """
        Build the initial hello/connection packet
        :param tid: Transaction id (usually 1, must be sent as first packet)
        :param client_string: Game client string (e.g. "bfbc2-pc")
        :return: Complete packet to establish connection
        """
        return Packet.build(
            b'CONN@\x00\x00\x00',
            b'PROT=2\nPROD=' + client_string + b'\nVERS=1.1\nPLAT=PC\nLOCALE=en_US\nSDKVERSION=5.0.0.0.0\nTID=' + tid
        )

    @staticmethod
    def build_user_packet(tid: bytes, lkey: bytes) -> Packet:
        """
        Build the user/login packet
        :param tid: Transaction id (usually 2, must be sent as second packet)
        :param lkey: Login key from a FESL session
        :return: Complete packet to perform login
        """
        return Packet.build(
            b'USER@\x00\x00\x00',
            b'MAC=$000000000000\nSKU=125170\nLKEY=' + lkey + b'\nNAME=\nTID=' + tid
        )

    @staticmethod
    def build_llst_packet(tid: bytes) -> Packet:
        """
        Build the llst/lobby list packet
        :param tid: Transaction id
        :return: Complete packet to list all available game lobbies
        """
        return Packet.build(
            b'LLST@\x00\x00\x00',
            b'FILTER-FAV-ONLY=0\nFILTER-NOT-FULL=0\nFILTER-NOT-PRIVATE=0\nFILTER-NOT-CLOSED=0\nFILTER-MIN-SIZE=0\n'
            b'FAV-PLAYER=\nFAV-GAME=\nFAV-PLAYER-UID=\nFAV-GAME-UID=\nTID=' + tid
        )

    @staticmethod
    def build_glst_packet(tid: bytes, lid: bytes) -> Packet:
        """
        Build the glst/game (server) list packet
        :param tid: Transaction id
        :param lid: Id of lobby to retrieve games from
        :return: Complete packet to list all available game servers in lobby
        """
        return Packet.build(
            b'GLST@\x00\x00\x00',
            b'LID=' + lid + b'\nTYPE=\nFILTER-FAV-ONLY=0\nFILTER-NOT-FULL=0\nFILTER-NOT-PRIVATE=0\n'
            b'FILTER-NOT-CLOSED=0\nFILTER-MIN-SIZE=0\nFAV-PLAYER=\nFAV-GAME=\nCOUNT=-1\nFAV-PLAYER-UID=\n'
            b'FAV-GAME-UID=\nTID=' + tid
        )

    @staticmethod
    def build_gdat_packet(tid: bytes, lid: bytes, gid: bytes) -> Packet:
        """
        Build the gdat/game (server) detailed data packet
        :param tid: Transaction id
        :param lid: Id of lobby the game server is hosted in
        :param gid: Id of the game server
        :return: Complete packet to retrieve detailed data for the game server
        """
        return Packet.build(
            b'GDAT@\x00\x00\x00',
            b'LID=' + lid + b'\nGID=' + gid + b'\nTID=' + tid
        )

    @staticmethod
    def is_valid_authentication_response(response: Packet) -> bool:
        return b'NAME=' in response.body
