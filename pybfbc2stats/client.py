import warnings
from base64 import b64encode, b64decode
from datetime import timedelta
from typing import List, Union, Dict, Tuple, Optional, Callable
from urllib.parse import quote_from_bytes, unquote_to_bytes

from .buffer import Buffer, ByteOrder
from .connection import SecureConnection, Connection
from .constants import STATS_KEYS, FRAGMENT_SIZE, FeslStep, Namespace, Platform, BACKEND_DETAILS, LookupType, \
    DEFAULT_LEADERBOARD_KEYS, Step, TheaterStep, FeslTransmissionType, TheaterTransmissionType, StructuredDataType, \
    EPOCH_START, ENCODING, FeslParseMap, TheaterParseMap
from .exceptions import ParameterError, Error, PlayerNotFoundError, \
    SearchError, AuthError, ServerNotFoundError, LobbyNotFoundError, RecordNotFoundError, ConnectionError, TimeoutError
from .packet import Packet, FeslPacket, TheaterPacket
from .payload import Payload, StrValue, IntValue, ParseMap


class Client:
    platform: Platform
    client_string: StrValue
    timeout: float
    track_steps: bool
    connection: Connection
    transaction_id: int
    completed_steps: Dict[Step, Packet]

    def __init__(
            self,
            connection: Connection,
            platform: Platform,
            client_string: StrValue,
            timeout: float = 3.0,
            track_steps: bool = True
    ):
        self.platform = platform
        self.client_string = client_string
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
                key = elements[0].decode(ENCODING)
                value = elements[1].decode(ENCODING)
                parsed[key] = value

        return parsed

    @staticmethod
    def dict_list_to_dict(dict_list: List[dict]) -> dict:
        sorted_list = sorted(dict_list, key=lambda x: x['key'])
        return {entry['key']: entry['value'] for entry in sorted_list}


class FeslClient(Client):
    username: StrValue
    password: StrValue
    connection: SecureConnection
    completed_steps: Dict[FeslStep, Packet]

    def __init__(self, username: StrValue, password: StrValue, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        connection = SecureConnection(
            BACKEND_DETAILS[platform]['host'],
            BACKEND_DETAILS[platform]['port'],
            FeslPacket
        )
        super().__init__(connection, platform, BACKEND_DETAILS[platform]['clientString'], timeout, track_steps)
        self.username = username
        self.password = password

    def __exit__(self, *excinfo):
        try:
            self.logout()
        except (ConnectionError, TimeoutError):
            pass
        self.connection.close()

    def hello(self) -> bytes:
        if self.track_steps and FeslStep.hello in self.completed_steps:
            return bytes(self.completed_steps[FeslStep.hello])

        tid = self.get_transaction_id()
        hello_packet = self.build_hello_packet(tid, self.client_string)
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

        response_valid, error_message, code = self.is_valid_login_response(response)
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
        payload = packet.get_payload()

        # Field is called "ip" but actually contains the hostname
        return payload.get_str('theaterIp', str()), payload.get_int('theaterPort', int())

    def get_lkey(self) -> str:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        packet = self.completed_steps[FeslStep.login]
        payload = packet.get_payload()

        return payload.get_str('lkey', str())

    def lookup_usernames(self, usernames: List[StrValue], namespace: Namespace) -> List[dict]:
        return self.lookup_user_identifiers(usernames, namespace, LookupType.byName)

    def lookup_username(self, username: StrValue, namespace: Namespace) -> dict:
        return self.lookup_user_identifier(username, namespace, LookupType.byName)

    def lookup_user_ids(self, user_ids: List[IntValue], namespace: Namespace) -> List[dict]:
        return self.lookup_user_identifiers(user_ids, namespace, LookupType.byId)

    def lookup_user_id(self, user_id: IntValue, namespace: Namespace) -> dict:
        return self.lookup_user_identifier(user_id, namespace, LookupType.byId)

    def lookup_user_identifiers(self, identifiers: List[Union[StrValue, IntValue]], namespace: Namespace,
                                lookup_type: LookupType) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        tid = self.get_transaction_id()
        lookup_packet = self.build_user_lookup_packet(tid, identifiers, namespace, lookup_type)
        self.connection.write(lookup_packet)

        payload = self.get_response(tid, parse_map=FeslParseMap.UserLookup)
        users = payload.get_list('userInfo', list())
        return users

    def lookup_user_identifier(self, identifier: Union[StrValue, IntValue], namespace: Namespace, lookup_type: LookupType) -> dict:
        results = self.lookup_user_identifiers([identifier], namespace, lookup_type)

        if len(results) == 0:
            raise PlayerNotFoundError('User lookup did not return any results')

        return results.pop()

    def search_name(self, screen_name: StrValue, namespace: Namespace) -> dict:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        tid = self.get_transaction_id()
        search_packet = self.build_search_packet(tid, screen_name, namespace)
        self.connection.write(search_packet)

        payload = self.get_response(tid, parse_map=FeslParseMap.NameSearch)
        return {
            'namespace': payload.get_str('nameSpaceId', str()),
            'users': payload.get_list('users', list())
        }

    def get_stats(self, userid: IntValue, keys: List[StrValue] = STATS_KEYS) -> dict:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        # Send query in chunks (using the same transaction id for all packets)
        tid = self.get_transaction_id()
        chunk_packets = self.build_stats_query_packets(tid, userid, keys)
        for chunk_packet in chunk_packets:
            self.connection.write(chunk_packet)

        payload = self.get_response(tid, parse_map=FeslParseMap.Stats)
        return self.dict_list_to_dict(payload.get_list('stats', list()))

    def get_leaderboard(self, min_rank: IntValue = 1, max_rank: IntValue = 50, sort_by: StrValue = 'score',
                        keys: List[StrValue] = DEFAULT_LEADERBOARD_KEYS) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        tid = self.get_transaction_id()
        leaderboard_packet = self.build_leaderboard_query_packet(tid, min_rank, max_rank, sort_by, keys)
        self.connection.write(leaderboard_packet)

        payload = self.get_response(tid, parse_map=FeslParseMap.Stats)
        # Turn sub lists into dicts and return result
        return [
            {
                key: Client.dict_list_to_dict(value) if isinstance(value, list) else value
                for (key, value) in entry.items()
            } for entry in payload.get_list('stats', list())
        ]

    def get_dogtags(self, userid: IntValue) -> List[dict]:
        if self.track_steps and FeslStep.login not in self.completed_steps:
            self.login()

        tid = self.get_transaction_id()
        dogtags_packet = self.build_dogtag_query_packet(tid, userid)
        self.connection.write(dogtags_packet)

        payload = self.get_response(tid)
        return self.format_dogtags_response(payload.get_map('values', dict()), self.platform)

    def is_auto_respond_packet(self, packet: Packet) -> Tuple[bool, Optional[Callable]]:
        txn = packet.get_payload().get('TXN')
        if txn == 'MemCheck':
            return True, self.memcheck
        elif txn == 'Ping':
            return True, self.ping

        return False, None

    def get_response(self, tid: int, parse_map: Optional[ParseMap] = None) -> Payload:
        response = bytes()
        last_packet = False
        while not last_packet:
            packet = self.wrapped_read(tid)
            data, last_packet = self.process_response_packet(packet)
            response += data

        return Payload.from_bytes(response, parse_map)

    @staticmethod
    def build_list_body(items: List[Union[bytes, Dict[bytes, bytes]]], prefix: bytes) -> bytes:
        warnings.warn(
            'The "build_list_body" method is deprecated, build packet bodies via "Payload" instead',
            DeprecationWarning
        )

        return bytes(Payload(**{
            prefix: items
        }))

    @staticmethod
    def build_list_item(dotted_elements: List[bytes], value: bytes) -> bytes:
        warnings.warn(
            'The "build_list_item" method is deprecated, build packet bodies via "Payload" instead',
            DeprecationWarning
        )

        return b'.'.join(dotted_elements) + b'=' + value

    @staticmethod
    def build_hello_packet(tid: int, client_string: StrValue) -> FeslPacket:
        return FeslPacket.build(
            b'fsys',
            Payload(
                TXN='Hello',
                clientString=client_string,
                sku='PC',
                locale='en_US',
                clientPlatform='PC',
                clientVersion='2.0',
                SDKVersion='5.1.2.0.0',
                protocolVersion='2.0',
                fragmentSize=FRAGMENT_SIZE,
                clientType='server'
            ),
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_memcheck_packet() -> FeslPacket:
        return FeslPacket.build(
            b'fsys',
            Payload(TXN='MemCheck', result=None),
            FeslTransmissionType.SinglePacketResponse
        )

    @staticmethod
    def build_login_packet(tid: int, username: StrValue, password: StrValue) -> FeslPacket:
        return FeslPacket.build(
            b'acct',
            Payload(
                TXN='Login',
                returnEncryptedInfo=0,
                name=username,
                password=password,
                macAddr='$000000000000'
            ),
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_logout_packet(tid: int) -> FeslPacket:
        return FeslPacket.build(
            b'fsys',
            Payload(TXN='Goodbye', reason='GOODBYE_CLIENT_NORMAL', message='"Disconnected via front-end"'),
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_ping_packet() -> FeslPacket:
        return FeslPacket.build(
            b'fsys',
            Payload(TXN='Ping'),
            FeslTransmissionType.SinglePacketResponse
        )

    @staticmethod
    def build_user_lookup_packet(
            tid: int,
            user_identifiers: List[Union[StrValue, IntValue]],
            namespace: Union[Namespace, bytes],
            lookup_type: Union[LookupType, bytes]
    ) -> FeslPacket:
        lookups = [
            {
                # TODO Update lookup type to str enum
                bytes(lookup_type).decode(ENCODING): identifier,
                'namespace': namespace
            } for identifier in user_identifiers
        ]

        payload = Payload(TXN='NuLookupUserInfo', userInfo=lookups)
        # Use LookupUserInfo instead of NuLookupUserInfo for legacy namespaces
        if Namespace.is_legacy_namespace(namespace):
            payload.set('TXN', 'LookupUserInfo')

        return FeslPacket.build(
            b'acct',
            payload,
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_search_packet(tid: int, screen_name: StrValue, namespace: Union[Namespace, StrValue]) -> FeslPacket:
        payload = Payload(
            TXN='NuSearchOwners',
            screenName=screen_name,
            searchType=1,
            retrieveUserIds=0,
            nameSpaceId=bytes(namespace)
        )
        # Use SearchOwners instead of NuSearchOwners for legacy namespaces
        if Namespace.is_legacy_namespace(namespace):
            payload.set('TXN', 'SearchOwners')
            payload.set('retrieveUserIds', 1)

        return FeslPacket.build(
            b'acct',
            payload,
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_leaderboard_query_packet(tid: int, min_rank: IntValue, max_rank: IntValue,
                                       sort_by: StrValue, keys: List[StrValue]) -> FeslPacket:
        payload = Payload(
            TXN='GetTopNAndStats',
            key=sort_by,
            ownerType=1,
            minRank=min_rank,
            maxRank=max_rank,
            periodId=0,
            periodPast=0,
            rankOrder=0,
            keys=keys
        )

        return FeslPacket.build(
            b'rank',
            payload,
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def build_stats_query_packets(tid: int, userid: IntValue, keys: List[StrValue]) -> List[FeslPacket]:
        payload = Payload(
            TXN='GetStats',
            owner=userid,
            ownerType=1,
            periodId=0,
            periodPast=0,
            keys=keys
        )

        if len(payload) <= FRAGMENT_SIZE:
            return [
                FeslPacket.build(
                    b'rank',
                    payload,
                    FeslTransmissionType.SinglePacketRequest,
                    tid
                )
            ]

        # Base64 encode query for transfer
        payload_b64 = b64encode(bytes(payload) + b'\x00')
        encoded_payload_size = str(len(payload_b64))

        # URL encode/quote query
        payload_enc = quote_from_bytes(payload_b64).encode(ENCODING)

        # Split query into chunks and build packets around them
        chunk_packets = []
        for i in range(0, len(payload_enc), FRAGMENT_SIZE):
            payload_chunk = payload_enc[i:i + FRAGMENT_SIZE]
            # TODO Add decoded size?
            chunk_packet = FeslPacket.build(
                b'rank',
                Payload(size=encoded_payload_size, data=payload_chunk),
                FeslTransmissionType.MultiPacketRequest,
                tid
            )
            chunk_packets.append(chunk_packet)

        return chunk_packets

    @staticmethod
    def build_dogtag_query_packet(tid: int, userid: IntValue) -> FeslPacket:
        return FeslPacket.build(
            b'recp',
            # Could also use GetRecord to receive a list
            Payload(TXN='GetRecordAsMap', recordName='dogtags', owner=userid),
            FeslTransmissionType.SinglePacketRequest,
            tid
        )

    @staticmethod
    def is_valid_login_response(response: Packet) -> Tuple[bool, str, int]:
        payload = response.get_payload()

        valid = payload.get('lkey') is not None
        if not valid:
            message = payload.get_str('localizedMessage')
            code = payload.get_int('errorCode')
        else:
            message = ''
            code = 0

        return valid, message, code

    @staticmethod
    def parse_list_response(raw_response: bytes, entry_prefix: bytes) -> Tuple[List[dict], List[bytes]]:
        warnings.warn(
            'The "parse_list_response" method is deprecated, parse packet bodies via "Payload" instead',
            DeprecationWarning
        )

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
            # line format will be something like: 0.userId=22680455
            elements = line.split(b'=')
            key_elements = elements[0].split(b'.')
            index = int(key_elements[0])
            key = key_elements[1].decode(ENCODING)
            value = elements[1].decode(ENCODING)
            # Add sub-list (99.addStats.9.value=777.678) or simple scalar value (99.value=8.367105024E9)
            if len(key_elements) >= 3 and b'.[]=' in line:
                # If line contains a sub-list length indicator, init sub list of given length
                datasets[index][key] = [{} for _ in range(0, int(value))]
            elif len(key_elements) >= 4:
                # Line contains sub-list data => append to list at index and key
                sub_index = int(key_elements[2])
                sub_key = key_elements[3].decode(ENCODING)
                datasets[index][key][sub_index][sub_key] = value
            else:
                # Add scalar value to dict
                datasets[index][key] = value

        return datasets, meta_lines

    @staticmethod
    def parse_map_response(raw_response: bytes, entry_prefix: bytes) -> Tuple[Dict[str, bytes], List[bytes]]:
        warnings.warn(
            'The "parse_map_response" method is deprecated, parse packet bodies via "Payload" instead',
            DeprecationWarning
        )

        data_lines, meta_lines, entry_count = FeslClient.pre_parse_complex_response(
            raw_response,
            entry_prefix,
            StructuredDataType.map
        )

        dataset = {}
        for line in data_lines:
            raw_key, _, raw_value = line.partition(b'=')
            # Remove map braces from key
            key = raw_key.strip(b'{}').decode(ENCODING)
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
        warnings.warn(
            'The "pre_parse_complex_response" method is deprecated, parse packet bodies via "Payload" instead',
            DeprecationWarning
        )

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
    def process_response_packet(packet: Packet) -> Tuple[bytes, bool]:
        # Fifth byte indicates whether packet is single/multi packet request/response or ping packet
        transmission_type = packet.get_transmission_type()
        payload = packet.get_payload()

        # Check for errors
        error_code = payload.get_int('errorCode')
        if error_code is not None:
            method = payload.get_str('TXN')
            error_message = payload.get_str('localizedMessage')
            if error_code == 21:
                raise ParameterError('FESL returned invalid parameter error')
            elif error_code == 101 and method == 'NuLookupUserInfo':
                raise PlayerNotFoundError('FESL returned player not found error')
            elif error_code == 101 and method == 'NuSearchOwners':
                raise SearchError('FESL returned player not found error')
            elif error_code == 104 and method == 'NuSearchOwners':
                # Error code is returned if a) no results matched the query or b) too many results matched the query
                # (the error message just says: "The data necessary for this transaction was not found")
                raise SearchError('FESL found no or too many results matching the search query')
            elif error_code == 223 and method == 'SearchOwners':
                # In contrast to NuSearchOwners, SearchOwners actually returns an empty list if no results are found,
                # so the error code is only related to finding too many results
                # (also indicated by the error message: "Too many results found, please refine the search criteria")
                raise SearchError('FESL found too many results matching the search query')
            elif error_code == 5000 and method.startswith('GetRecord'):
                raise RecordNotFoundError('FESL returned record not found error')
            else:
                raise Error(f'FESL returned an error: {error_message} (code {error_code})')
        elif transmission_type is not FeslTransmissionType.SinglePacketResponse and \
                transmission_type is not FeslTransmissionType.MultiPacketResponse:
            # Packet is neither one data packet of a multi-packet response nor a single-packet response
            raise Error('FESL returned invalid response')

        if transmission_type is FeslTransmissionType.MultiPacketResponse:
            # Packet is one of multiple => base64 decode content
            # URL decode/unquote and base64 decode data
            data = b64decode(unquote_to_bytes(payload.get('data')))
            # Remove "eof" indicator from last packet's data
            last_packet = data[-1:] == b'\x00'
            # Cannot return a payload here because the packet might be split into chunks in the middle of a key/value
            # Creating a payload from such a chunk would result in the following chunk not being appended correctly
            if last_packet:
                return data[:-1], True
            return data, False

        # Single packet response => return body as is
        return packet.body, True

    @staticmethod
    def format_search_response(parsed_response: List[dict], metadata: List[bytes]) -> dict:
        warnings.warn('The "format_search_response" method is deprecated', DeprecationWarning)

        namespace_line = next(line for line in metadata if line.startswith(b'nameSpaceId'))
        namespace = namespace_line.split(b'=').pop()

        return {
            'namespace': namespace.decode(ENCODING),
            'users': parsed_response
        }

    @staticmethod
    def format_dogtags_response(parsed_response: Dict[str, bytes], platform: Platform) -> List[dict]:
        results = []
        for key, value in parsed_response.items():
            """
            Value format seems a bit odd here (who knows, maybe it was obvious do whoever built it at DICE)
            Note: Different platforms (seem to) use different byte orders (ps3: big, pc: little)
            Total record length is 28 bytes (BC2)/24 bytes (BC), structured as:
            - 16 bytes, player name, padded to length using null bytes if required
            - 4 bytes, meaning unknown (could be an int [timestamp?],
              since order seems to be flipped on PC vs. PS3 => byte order)
            - 6 bytes (BC2) or 2 bytes (BC), number of dogtags taken from player
            - 1 byte, player rank (at time of [last?] dogtag taken)
            - 1 byte, meaning unknown (seems to always be \x00, so it may just be an end marker)
            """
            byte_order = ByteOrder.LittleEndian if platform is Platform.pc else ByteOrder.BigEndian
            buffer = Buffer(value, byte_order)
            raw_name = buffer.read(16)
            timestamp = EPOCH_START + timedelta(days=buffer.read_float())
            dogtags = FeslClient.extract_dogtags(buffer)
            rank = buffer.read_uchar()

            results.append({
                'userId': int(key),
                # FESL returns mangled, incorrect names in extremely rare cases
                # e.g. b'\xac\x1d5\x08Dvil07\x00\x00\x00\x00\x00\x00' for pid battlefield/272333965,
                # whose actual name is 'DarkDvil07' as per a direct lookup
                # => ignore any decoding errors
                'userName': raw_name.strip(b'\x00').decode(ENCODING, 'replace'),
                'timestamp': timestamp.timestamp(),
                'rank': rank,
                **dogtags,
                'raw': value
            })

        return results

    @staticmethod
    def extract_dogtags(buffer: Buffer) -> dict:
        length = len(buffer.remaining())
        if length == 4:
            """
            Bad Company only tracks the total and seemingly determines bronze/silver/gold based on rank value
            So, we only get:
            - 2 bytes, number of dogtags taken from player
            """
            #
            total = buffer.read_ushort()
            return {
                'dogtags': total
            }

        if length == 8:
            """
            Bad Company 2 returns individual values for the different dogtag tiers:
            - 2 bytes, number of bronze dogtags taken from player
            - 2 bytes, number of silver dogtags taken from player
            - 2 bytes, number of gold dogtags taken from player
            """
            gold, silver, bronze = buffer.read_ushort(), buffer.read_ushort(), buffer.read_ushort()
            total = bronze + silver + gold
            return {
                'bronze': bronze,
                'silver': silver,
                'gold': gold,
                'dogtags': total
            }

        raise Error('Trying to extract dogtag from record with invalid remaining length')

class TheaterClient(Client):
    lkey: StrValue
    completed_steps: Dict[TheaterStep, Packet]

    def __init__(self, host: str, port: int, lkey: StrValue, platform: Platform, timeout: float = 3.0,
                 track_steps: bool = True):
        connection = Connection(host, port, TheaterPacket)
        super().__init__(connection, platform, BACKEND_DETAILS[platform]['clientString'], timeout, track_steps)
        self.lkey = lkey

    def connect(self) -> bytes:
        """
        Initialize the connection to the Theater backend by sending the initial CONN/hello packet
        :return: Response packet data
        """
        if self.track_steps and TheaterStep.conn in self.completed_steps:
            return bytes(self.completed_steps[TheaterStep.conn])

        tid = self.get_transaction_id()
        connect_packet = self.build_conn_packet(tid, self.client_string)
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
        llst = llst_response.get_payload()
        num_lobbies = llst.get_int('NUM-LOBBIES', int())

        # Retrieve given number of lobbies (usually just one these days)
        lobbies = []
        for i in range(num_lobbies):
            ldat_response = self.wrapped_read(tid)
            ldat = ldat_response.get_payload(TheaterParseMap.LDAT)
            lobbies.append(dict(ldat))

        return lobbies

    def get_servers(self, lobby_id: IntValue) -> List[dict]:
        """
        Retrieve all available game servers from the given lobby
        :param lobby_id: Id of the game server lobby
        :return: List of server details
        """
        if self.track_steps and TheaterStep.user not in self.completed_steps:
            self.authenticate()

        tid = self.get_transaction_id()
        server_list_packet = self.build_glst_packet(tid, lobby_id)
        self.connection.write(server_list_packet)

        # Again, same procedure: Theater first responds with a GLST packet which indicates the number of games/servers
        # in the lobby. It then sends one GDAT packet per game/server
        glst_response = self.wrapped_read(tid)
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
            gdat_response = self.wrapped_read(tid)
            gdat = gdat_response.get_payload(TheaterParseMap.GDAT)
            servers.append(dict(gdat))

        return servers

    def get_server_details(self, lobby_id: IntValue, game_id: IntValue) -> Tuple[dict, dict, List[dict]]:
        """
        Retrieve full details and player list for a given server
        :param lobby_id: Id of the game server lobby the server is hosted in
        :param game_id: Game (server) id
        :return: Tuple of (general server details, extended details, player list)
        """
        return self.get_gdat(LID=lobby_id, GID=game_id)

    def get_current_server(self, user_id: IntValue) -> Tuple[dict, dict, List[dict]]:
        """
        Retrieve full details and player list for a given user's current server (server they are currently playing on,
        raises a PlayerNotFound exception if the player is not currently playing online)
        :param user_id: Id of the user whose current server to get
        :return: Tuple of (general server details, extended details, player list)
        """
        return self.get_gdat(UID=user_id)

    def get_gdat(self, **kwargs: IntValue) -> Tuple[dict, dict, List[dict]]:
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
        gdat = gdat_response.get_payload(TheaterParseMap.GDAT)
        gdet_response = self.wrapped_read(tid)
        gdet = gdet_response.get_payload(TheaterParseMap.GDET)

        # Determine number of active players (AP)
        num_players = gdat.get_int('AP', int())
        # Read PDAT packets for all players
        players = []
        for i in range(num_players):
            pdat_response = self.wrapped_read(tid)
            pdat = pdat_response.get_payload(TheaterParseMap.PDAT)
            players.append(dict(pdat))

        return dict(gdat), dict(gdet), players

    def is_auto_respond_packet(self, packet: Packet) -> Tuple[bool, Optional[Callable]]:
        if packet.header.startswith(b'PING'):
            return True, self.ping

        return False, None

    @staticmethod
    def build_conn_packet(tid: int, client_string: StrValue) -> TheaterPacket:
        """
        Build the initial hello/connection packet
        :param tid: Transaction id (usually 1, must be sent as first packet)
        :param client_string: Game client string (e.g. "bfbc2-pc")
        :return: Complete packet to establish connection
        """
        return TheaterPacket.build(
            b'CONN',
            Payload(PROT=2, PROD=client_string, VERS='1.0', PLAT='PS3', LOCALE='en_US', SDKVERSION='5.1.2.0.0'),
            TheaterTransmissionType.Request,
            tid
        )

    @staticmethod
    def build_user_packet(tid: int, lkey: StrValue) -> TheaterPacket:
        """
        Build the user/login packet
        :param tid: Transaction id (usually 2, must be sent as second packet)
        :param lkey: Login key from a FESL session
        :return: Complete packet to perform login
        """
        return TheaterPacket.build(
            b'USER',
            Payload(MAC='$000000000000', SKU=125170, LKEY=lkey, NAME=None),
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
            Payload(),
            TheaterTransmissionType.Request,
            0
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
            Payload(**{
                'FILTER-FAV-ONLY': 0,
                'FILTER-NOT-FULL': 0,
                'FILTER-NOT-PRIVATE': 0,
                'FILTER-NOT-CLOSED': 0,
                'FILTER-MIN-SIZE': 0,
                'FAV-PLAYER': None,
                'FAV-GAME': None,
                'FAV-PLAYER-UID': None,
                'FAV-GAME-UID': None
            }),
            TheaterTransmissionType.Request,
            tid
        )

    @staticmethod
    def build_glst_packet(tid: int, lid: IntValue) -> TheaterPacket:
        """
        Build the glst/game (server) list packet
        :param tid: Transaction id
        :param lid: Id of lobby to retrieve games from
        :return: Complete packet to list all available game servers in lobby
        """
        return TheaterPacket.build(
            b'GLST',
            Payload(**{
                'LID': lid,
                'TYPE': None,
                'FILTER-FAV-ONLY': 0,
                'FILTER-NOT-FULL': 0,
                'FILTER-NOT-PRIVATE': 0,
                'FILTER-NOT-CLOSED': 0,
                'FILTER-MIN-SIZE': 0,
                'FAV-PLAYER': None,
                'FAV-GAME': None,
                'FAV-PLAYER-UID': None,
                'FAV-GAME-UID': None,
                'COUNT': -1
            }),
            TheaterTransmissionType.Request,
            tid
        )

    @staticmethod
    def build_gdat_packet(tid: int, **kwargs: IntValue) -> TheaterPacket:
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
            Payload(**kwargs),
            TheaterTransmissionType.Request,
            tid
        )

    @staticmethod
    def is_valid_authentication_response(response: Packet) -> bool:
        return response.get_payload().get('NAME') is not None

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
