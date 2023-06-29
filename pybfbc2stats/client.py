from base64 import b64encode, b64decode
from typing import List, Union, Dict, Tuple, Optional, Callable
from urllib.parse import quote_from_bytes, unquote_to_bytes

from .buffer import Buffer, ByteOrder
from .connection import SecureConnection, Connection
from .constants import STATS_KEYS, DEFAULT_BUFFER_SIZE, FeslStep, Namespace, Platform, BACKEND_DETAILS, LookupType, \
    DEFAULT_LEADERBOARD_KEYS, Step, TheaterStep, FeslTransmissionType, TheaterTransmissionType, StructuredDataType
from .exceptions import ParameterError, Error, PlayerNotFoundError, \
    SearchError, AuthError, ServerNotFoundError, LobbyNotFoundError, RecordNotFoundError
from .packet import Packet, FeslPacket, TheaterPacket


class Client:
    platform: Platform
    timeout: float
    track_steps: bool
    connection: Connection
    transaction_id: int
    completed_steps: Dict[Step, Packet]

    def __init__(self, connection: Connection, platform: Platform, timeout: float = 3.0, track_steps: bool = True):
        self.platform = platform
        self.track_steps = track_steps
        self.connection = connection
        # Using the client with too short of a timeout leads to lots if issues with reads timing out and subsequent
        # reads then reading data from the previous "request" => enforce minimum timeout of 2 seconds
        self.connection.timeout = max(timeout, 2.0)
        self.transaction_id = 0
        self.completed_steps = {}

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        self.connection.close()

    def wrapped_read(self, tid: int) -> Packet:
        """
        Read a single packet from the connection and automatically respond plus read next packet if the initial packet
        was one that requires an immediate response (memcheck, ping)
        :return: A packet containing "real" data
        """
        initial_packet = self.connection.read()

        # Check packet is not a "real" data packet but one that prompts a response (memcheck, ping)
        auto_respond, handler = self.is_auto_respond_packet(initial_packet)
        if auto_respond:
            # Call auto respond handler
            handler()
            # Call self to read another packet
            data_packet = self.wrapped_read(tid)
        elif initial_packet.get_tid() < tid:
            # Call self to read another packet if packet is not part of current transaction
            data_packet = self.wrapped_read(tid)
        else:
            data_packet = initial_packet

        return data_packet

    def get_transaction_id(self) -> int:
        """
        "Assign" a transaction id (FESL sends them as part of the header for all but memcheck and ping packets)
        :return: Transaction id as int
        """
        self.transaction_id += 1
        return self.transaction_id

    def is_auto_respond_packet(self, packet: Packet) -> Tuple[bool, Optional[Callable]]:
        pass

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
            BACKEND_DETAILS[platform]['port'],
            FeslPacket
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

        tid = self.get_transaction_id()
        hello_packet = self.build_hello_packet(tid, BACKEND_DETAILS[self.platform]['clientString'])
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

        tid = self.get_transaction_id()
        login_packet = self.build_login_packet(tid, self.username, self.password)
        self.connection.write(login_packet)
        response = self.wrapped_read(tid)

        response_valid, error_message = self.is_valid_login_response(response)
        if not response_valid:
            raise AuthError(error_message)

        self.completed_steps[FeslStep.login] = response

        return bytes(response)

    def logout(self) -> Optional[bytes]:
        if self.track_steps and FeslStep.login in self.completed_steps:
            tid = self.get_transaction_id()
            logout_packet = self.build_logout_packet(tid)
            self.connection.write(logout_packet)
            self.completed_steps.clear()
            return bytes(self.wrapped_read(tid))

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

        tid = self.get_transaction_id()
        lookup_packet = self.build_user_lookup_packet(tid, identifiers, namespace, lookup_type)
        self.connection.write(lookup_packet)

        raw_response = self.get_complex_response(tid)
        parsed_response, _ = self.parse_list_response(raw_response, b'userInfo.')
        return parsed_response

    def lookup_user_identifier(self, identifier: str, namespace: Namespace, lookup_type: LookupType) -> dict:
        results = self.lookup_user_identifiers([identifier], namespace, lookup_type)

        if len(results) == 0:
            raise PlayerNotFoundError('User lookup did not return any results')

        return results.pop()

    def search_name(self, screen_name: str, namespace: Namespace) -> dict:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        tid = self.get_transaction_id()
        search_packet = self.build_search_packet(tid, screen_name, namespace)
        self.connection.write(search_packet)

        raw_response = self.get_complex_response(tid)
        parsed_response, metadata = self.parse_list_response(raw_response, b'users.')
        return self.format_search_response(parsed_response, metadata)

    def get_stats(self, userid: int, keys: List[bytes] = STATS_KEYS) -> dict:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        # Send query in chunks (using the same transaction id for all packets)
        tid = self.get_transaction_id()
        chunk_packets = self.build_stats_query_packets(tid, userid, keys)
        for chunk_packet in chunk_packets:
            self.connection.write(chunk_packet)

        raw_response = self.get_complex_response(tid)
        parsed_response, *_ = self.parse_list_response(raw_response, b'stats.')
        return self.dict_list_to_dict(parsed_response)

    def get_leaderboard(self, min_rank: int = 1, max_rank: int = 50, sort_by: bytes = b'score',
                        keys: List[bytes] = DEFAULT_LEADERBOARD_KEYS) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        tid = self.get_transaction_id()
        leaderboard_packet = self.build_leaderboard_query_packet(tid, min_rank, max_rank, sort_by, keys)
        self.connection.write(leaderboard_packet)

        raw_response = self.get_complex_response(tid)
        parsed_response, *_ = self.parse_list_response(raw_response, b'stats.')
        # Turn sub lists into dicts and return result
        return [{key: self.dict_list_to_dict(value) if isinstance(value, list) else value
                 for (key, value) in persona.items()} for persona in parsed_response]

    def get_dogtags(self, userid: int) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        tid = self.get_transaction_id()
        dogtags_packet = self.build_dogtag_query_packet(tid, userid)
        self.connection.write(dogtags_packet)

        raw_response = self.get_complex_response(tid)
        parsed_response, *_ = self.parse_map_response(raw_response, b'values.')
        return self.format_dogtags_response(parsed_response, self.platform)


    def is_auto_respond_packet(self, packet: Packet) -> Tuple[bool, Optional[Callable]]:
        is_auto_respond_packet, handler = False, None

        # Check if packet is a memcheck/ping prompt
        if b'TXN=MemCheck' in packet.body:
            is_auto_respond_packet = True
            handler = self.memcheck
        elif b'TXN=Ping' in packet.body:
            is_auto_respond_packet = True
            handler = self.ping

        return is_auto_respond_packet, handler

    def get_complex_response(self, tid: int) -> bytes:
        response = b''
        last_packet = False
        while not last_packet:
            packet = self.wrapped_read(tid)
            data, last_packet = self.process_complex_response_packet(packet)
            response += data

        return response

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
    def build_hello_packet(tid: int, client_string: bytes) -> FeslPacket:
        return FeslPacket.build(
            b'fsys',
            b'TXN=Hello\nclientString=' + client_string +
            b'\nsku=PC\nlocale=en_US\nclientPlatform=PC\nclientVersion=2.0\nSDKVersion=5.1.2.0.0\nprotocolVersion=2.0\n'
            b'fragmentSize=8096\nclientType=server',
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_memcheck_packet() -> FeslPacket:
        return FeslPacket.build(
            b'fsys',
            b'TXN=MemCheck\nresult=',
            FeslTransmissionType.SinglePacketResponse
        )

    @staticmethod
    def build_login_packet(tid: int, username: bytes, password: bytes) -> FeslPacket:
        return FeslPacket.build(
            b'acct',
            b'TXN=Login\nreturnEncryptedInfo=0\n'
            b'name=' + username + b'\npassword=' + password + b'\nmacAddr=$000000000000',
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_logout_packet(tid: int) -> FeslPacket:
        return FeslPacket.build(
            b'fsys',
            b'TXN=Goodbye\nreason=GOODBYE_CLIENT_NORMAL\nmessage="Disconnected via front-end"',
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_ping_packet() -> FeslPacket:
        return FeslPacket.build(
            b'fsys',
            b'TXN=Ping',
            FeslTransmissionType.SinglePacketResponse
        )

    @staticmethod
    def build_user_lookup_packet(tid: int, user_identifiers: List[str],
                                 namespace: Namespace, lookup_type: LookupType) -> FeslPacket:
        user_dicts = [{bytes(lookup_type): identifier.encode('utf8'), b'namespace': bytes(namespace)}
                      for identifier in user_identifiers]
        lookup_list = FeslClient.build_list_body(user_dicts, b'userInfo')
        return FeslPacket.build(
            b'acct',
            b'TXN=NuLookupUserInfo\n' + lookup_list,
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_search_packet(tid: int, screen_name: str, namespace: Namespace) -> FeslPacket:
        return FeslPacket.build(
            b'acct',
            b'TXN=NuSearchOwners\nscreenName=' + screen_name.encode('utf8') + b'\nsearchType=1\nretrieveUserIds=0\n'
            b'nameSpaceId=' + bytes(namespace),
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_leaderboard_query_packet(tid: int, min_rank: int, max_rank: int,
                                       sort_by: bytes, keys: List[bytes]) -> FeslPacket:
        key_list = FeslClient.build_list_body(keys, b'keys')
        return FeslPacket.build(
            b'rank',
            b'TXN=GetTopNAndStats\nkey=' + sort_by + b'\nownerType=1\nminRank=' + str(min_rank).encode('utf8') +
            b'\nmaxRank=' + str(max_rank).encode('utf8') + b'\nperiodId=0\nperiodPast=0\nrankOrder=0\n' + key_list,
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_stats_query_packets(tid: int, userid: int, keys: List[bytes]) -> List[FeslPacket]:
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
            chunk_packet = FeslPacket.build(
                b'rank',
                b'size=' + encoded_query_size.encode('utf8') + b'\ndata=' + query_chunk,
                FeslTransmissionType.MultiPacketRequest,
                tid
            )
            chunk_packets.append(chunk_packet)

        return chunk_packets

    @staticmethod
    def build_dogtag_query_packet(tid: int, userid: int) -> FeslPacket:
        return FeslPacket.build(
            b'recp',
            # Could also use GetRecord to receive a list
            b'TXN=GetRecordAsMap\nrecordName=dogtags\nowner=' + str(userid).encode('utf8'),
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

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
    def parse_list_response(raw_response: bytes, entry_prefix: bytes) -> Tuple[List[dict], List[bytes]]:
        data_lines, meta_lines, entry_count = FeslClient.pre_parse_complex_response(
            raw_response,
            entry_prefix,
            StructuredDataType.list
        )

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
    def parse_map_response(raw_response: bytes, entry_prefix: bytes) -> Tuple[Dict[str, bytes], List[bytes]]:
        data_lines, meta_lines, entry_count = FeslClient.pre_parse_complex_response(
            raw_response,
            entry_prefix,
            StructuredDataType.map
        )

        dataset = {}
        for line in data_lines:
            raw_key, _, raw_value = line.partition(b'=')
            # Remove map braces from key
            key = raw_key.strip(b'{}').decode()
            # Values are URL quoted and b64 encoded (in addition to the data in the packet being quoted and encoded)
            value = b64decode(unquote_to_bytes(raw_value))
            dataset[key] = value

        return dataset, meta_lines


    @staticmethod
    def pre_parse_complex_response(
            raw_response: bytes,
            entry_prefix: bytes,
            structure: StructuredDataType
    ) -> Tuple[List[bytes], List[bytes], int]:
        lines = raw_response.split(b'\n')
        # Assign lines to either data or meta lines
        meta_lines = []
        data_lines = []
        for line in lines:
            if line.startswith(entry_prefix) and entry_prefix + structure not in line:
                # Append data line (without entry prefix)
                # So for userInfo.0.userId=226804555, only add 0.userId=226804555 (assuming prefix is userInfo.)
                data_lines.append(line[len(entry_prefix):])
            else:
                # Add meta data lines as is
                meta_lines.append(line)

        # Determine data entry count
        length_info = next(line for line in meta_lines if b'.' + structure in line)
        entry_count = int(length_info.split(b'=').pop())

        return data_lines, meta_lines, entry_count

    @staticmethod
    def process_complex_response_packet(packet: Packet) -> Tuple[bytes, bool]:
        # Fifth byte indicates whether packet is single/multi packet request/response or ping packet
        transmission_type = packet.get_transmission_type()
        body = packet.get_data()
        lines = packet.get_data_lines()

        # Check for errors
        if b'errorCode' in body:
            method_line = next((line for line in lines if line.startswith(b'TXN')), b'')
            method = method_line.split(b'=').pop()
            error_code_line = next((line for line in lines if line.startswith(b'errorCode=')), b'')
            error_code = error_code_line.split(b'=').pop()
            if error_code == b'21':
                raise ParameterError('FESL returned invalid parameter error')
            elif error_code == b'101' and method == b'NuLookupUserInfo':
                raise PlayerNotFoundError('FESL returned player not found error')
            elif error_code == b'104' and method == b'NuSearchOwners':
                # Error code is returned if a) no results matched the query or b) too many results matched the query
                raise SearchError('FESL found no or too many results matching the search query')
            elif error_code == b'5000' and method.startswith(b'GetRecord'):
                raise RecordNotFoundError('FESL returned record not found error')
            else:
                raise Error(f'FESL returned an error (code {error_code.decode("utf")})')
        elif transmission_type is not FeslTransmissionType.SinglePacketResponse and \
                transmission_type is not FeslTransmissionType.MultiPacketResponse:
            # Packet is neither one data packet of a multi-packet response nor a single-packet response
            raise Error('FESL returned invalid response')

        if transmission_type is FeslTransmissionType.MultiPacketResponse:
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

    @staticmethod
    def format_dogtags_response(parsed_response: Dict[str, bytes], platform: Platform) -> List[dict]:
        results = []
        for key, value in parsed_response.items():
            """
            Value format seems a bit odd here (who knows, maybe it was obvious do whoever built it at DICE)
            Note: Different platforms (seem to) use different byte orders (ps3: big, pc: little)
            - player name, often but not always followed by a bunch of null bytes
            - 4 bytes, meaning unknown (could be an int [record id?], since order seems to be flipped on PC vs. PS3 => byte order)
            - 2 bytes, number of bronze dogtags taken from player
            - 2 bytes, number of silver dogtags taken from player
            - 2 bytes, number of gold dogtags taken from player
            - 2 bytes, meaning unknown
            Since there seems to no delimiter or anything for the name, we cannot determine it's length
            => just read from in reverse and take remainder as name (stripping the null bytes)
            """
            byte_order = ByteOrder.LittleEndian if platform is Platform.pc else ByteOrder.BigEndian
            buffer = Buffer(value, byte_order)
            buffer.reverse()
            buffer.skip(2)
            bronze, silver, gold = buffer.read_ushort(), buffer.read_ushort(), buffer.read_ushort()
            buffer.skip(4)
            raw_name = buffer.remaining()
            results.append({
                'userId': key,
                # FESL returns mangled, incorrect names in extremely rare cases
                # e.g. b'\xac\x1d5\x08Dvil07\x00\x00\x00\x00\x00\x00' for pid battlefield/272333965,
                # whose actual name is 'DarkDvil07' as per a direct lookup
                # => ignore any decoding errors
                'userName': raw_name.strip(b'\x00').decode('utf8', 'ignore'),
                'bronze': bronze,
                'silver': silver,
                'gold': gold
            })

        return results


class TheaterClient(Client):
    lkey: bytes
    completed_steps: Dict[TheaterStep, Packet]

    def __init__(self, host: str, port: int, lkey: str, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        connection = Connection(host, port, TheaterPacket)
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
            raise AuthError('Theater authentication failed')

        self.completed_steps[TheaterStep.user] = response

        return bytes(response)

    def ping(self) -> None:
        ping_packet = self.build_ping_packet()
        self.connection.write(ping_packet)

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
        llst_response = self.wrapped_read(tid)
        llst = self.parse_simple_response(llst_response)
        num_lobbies = int(llst['NUM-LOBBIES'])

        # Retrieve given number of lobbies (usually just one these days)
        lobbies = []
        for i in range(num_lobbies):
            ldat_response = self.wrapped_read(tid)
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
        glst_response = self.wrapped_read(tid)
        # Response may indicate an error if given lobby id does not exist
        is_error, error = self.is_error_response(glst_response)
        if is_error:
            raise error
        glst = self.parse_simple_response(glst_response)
        num_games = int(glst['LOBBY-NUM-GAMES'])

        # Retrieve GDAT for all servers
        servers = []
        for i in range(num_games):
            gdat_response = self.wrapped_read(tid)
            gdat = self.parse_simple_response(gdat_response)
            servers.append(gdat)

        return servers

    def get_server_details(self, lobby_id: int, game_id: int) -> Tuple[dict, dict, List[dict]]:
        """
        Retrieve full details and player list for a given server
        :param lobby_id: Id of the game server lobby the server is hosted in
        :param game_id: Game (server) id
        :return: Tuple of (general server details, extended details, player list)
        """
        return self.get_gdat(lid=str(lobby_id).encode('utf8'), gid=str(game_id).encode('utf8'))

    def get_current_server(self, user_id: int) -> Tuple[dict, dict, List[dict]]:
        """
        Retrieve full details and player list for a given user's current server (server they are currently playing on,
        raises a PlayerNotFound exception if the player is not currently playing online)
        :param user_id: Id of the user whose current server to get
        :return: Tuple of (general server details, extended details, player list)
        """
        return self.get_gdat(uid=str(user_id).encode('utf8'))

    def get_gdat(self, **kwargs: bytes)  -> Tuple[dict, dict, List[dict]]:
        """
        Get GDAT for an individual server
        :param kwargs: Id(s) to identify the game (server):
            a) id of lobby the game server is hosted in (lid) and Id of the game server or (gid)
            b) id of user for which the current server should be returned (uid)
        :return: Tuple of (general server details, extended details, player list)
        """
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            self.authenticate()

        tid = self.get_transaction_id()
        server_details_packet = self.build_gdat_packet(
            tid,
            **kwargs
        )
        self.connection.write(server_details_packet)

        # Similar structure to before, but with one difference: Theater returns a GDAT packet (general game data),
        # followed by a GDET packet (extended server data). Finally, it sends a PDAT packet for every player
        gdat_response = self.wrapped_read(tid)
        # Response may indicate an error if given lobby id and /or game id do not exist
        is_error, error = self.is_error_response(gdat_response)
        if is_error:
            raise error
        gdat = self.parse_simple_response(gdat_response)
        gdet_response = self.wrapped_read(tid)
        gdet = self.parse_simple_response(gdet_response)

        # Determine number of active players (AP)
        num_players = int(gdat['AP'])
        # Read PDAT packets for all players
        players = []
        for i in range(num_players):
            pdat_response = self.wrapped_read(tid)
            pdat = self.parse_simple_response(pdat_response)
            players.append(pdat)

        return gdat, gdet, players

    def is_auto_respond_packet(self, packet: Packet) -> Tuple[bool, Optional[Callable]]:
        is_auto_respond_packet, handler = False, None

        # Check if packet is a ping prompt
        if packet.header.startswith(b'PING'):
            is_auto_respond_packet = True
            handler = self.ping

        return is_auto_respond_packet, handler

    @staticmethod
    def build_conn_paket(tid: int, client_string: bytes) -> TheaterPacket:
        """
        Build the initial hello/connection packet
        :param tid: Transaction id (usually 1, must be sent as first packet)
        :param client_string: Game client string (e.g. "bfbc2-pc")
        :return: Complete packet to establish connection
        """
        return TheaterPacket.build(
            b'CONN',
            b'PROT=2\nPROD=' + client_string + b'\nVERS=1.0\nPLAT=PC\nLOCALE=en_US\nSDKVERSION=5.1.2.0.0',
            TheaterTransmissionType.Request,
            tid
        )

    @staticmethod
    def build_user_packet(tid: int, lkey: bytes) -> TheaterPacket:
        """
        Build the user/login packet
        :param tid: Transaction id (usually 2, must be sent as second packet)
        :param lkey: Login key from a FESL session
        :return: Complete packet to perform login
        """
        return TheaterPacket.build(
            b'USER',
            b'MAC=$000000000000\nSKU=125170\nLKEY=' + lkey + b'\nNAME=',
            TheaterTransmissionType.Request,
            tid
        )

    @staticmethod
    def build_ping_packet() -> TheaterPacket:
        """
        Build a ping response packet
        :return: Complete packet to respond to ping with
        """
        return TheaterPacket.build(
            b'PING',
            b'TID=0',
            TheaterTransmissionType.Request
        )

    @staticmethod
    def build_llst_packet(tid: int) -> TheaterPacket:
        """
        Build the llst/lobby list packet
        :param tid: Transaction id
        :return: Complete packet to list all available game lobbies
        """
        return TheaterPacket.build(
            b'LLST',
            b'FILTER-FAV-ONLY=0\nFILTER-NOT-FULL=0\nFILTER-NOT-PRIVATE=0\nFILTER-NOT-CLOSED=0\nFILTER-MIN-SIZE=0\n'
            b'FAV-PLAYER=\nFAV-GAME=\nFAV-PLAYER-UID=\nFAV-GAME-UID=',
            TheaterTransmissionType.Request,
            tid
        )

    @staticmethod
    def build_glst_packet(tid: int, lid: bytes) -> TheaterPacket:
        """
        Build the glst/game (server) list packet
        :param tid: Transaction id
        :param lid: Id of lobby to retrieve games from
        :return: Complete packet to list all available game servers in lobby
        """
        return TheaterPacket.build(
            b'GLST',
            b'LID=' + lid + b'\nTYPE=\nFILTER-FAV-ONLY=0\nFILTER-NOT-FULL=0\nFILTER-NOT-PRIVATE=0\n'
            b'FILTER-NOT-CLOSED=0\nFILTER-MIN-SIZE=0\nFAV-PLAYER=\nFAV-GAME=\nCOUNT=-1\nFAV-PLAYER-UID=\n'
            b'FAV-GAME-UID=',
            TheaterTransmissionType.Request,
            tid
        )

    @staticmethod
    def build_gdat_packet(tid: int, **kwargs: bytes) -> TheaterPacket:
        """
        Build the gdat/game (server) detailed data packet
        :param tid: Transaction id
        :param kwargs: Id(s) to identify the game (server):
            a) id of lobby the game server is hosted in (lid) and Id of the game server or (gid)
            b) id of user for which the current server should be returned (uid)
        :return: Complete packet to retrieve detailed data for the game server
        """
        return TheaterPacket.build(
            b'GDAT',
            b'\n'.join(
                key.upper().encode('utf8') + b'=' + value
                for (key, value) in kwargs.items()
            ),
            TheaterTransmissionType.Request,
            tid
        )

    @staticmethod
    def is_valid_authentication_response(response: Packet) -> bool:
        return b'NAME=' in response.body

    @staticmethod
    def is_error_response(response: Packet) -> Tuple[bool, Optional[Error]]:
        is_error, error = False, None
        if response.header.startswith(b'GLSTnrom'):
            # Theater returns a header starting with b'GLSTnrom' ("no room"?, room=lobby?) if the given
            # lobby_id does not exist (only applies to retrieving server lists from lobby,
            # individual server queries return the below b'GDATngam' instead)
            is_error, error = True, LobbyNotFoundError('Theater returned lobby not found error')
        elif response.header.startswith(b'GDATngam'):
            # Theater returns a header starting with b'GDATngam' ("no game"?) if the given
            # lobby_id-game_id combination does not exist
            is_error, error = True, ServerNotFoundError('Theater returned server not found error')
        elif response.header.startswith(b'GDATntfn'):
            # Theater return a header starting with b'GDATntfn' ("not found"?) both if the user whose uid was given
            # is not currently playing on any server and if no user with that id exists
            is_error, error = True, PlayerNotFoundError('Theater returned player not found/not online error')
        elif response.header[4:8] == b'bpar':
            # Theater returns a header containing b'bpar' if parameters are not provided correctly
            is_error, error = True, ParameterError('Theater returned bad parameter error')

        return is_error, error
