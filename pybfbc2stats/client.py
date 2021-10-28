from base64 import b64encode, b64decode
from typing import List, Union, Dict
from urllib.parse import quote_from_bytes, unquote_to_bytes

from .connection import Connection
from .constants import STATS_KEYS, BUFFER_SIZE, Step, Namespace, Platform, FESL_DETAILS
from .exceptions import PyBfbc2StatsParameterError, PyBfbc2StatsError, PyBfbc2StatsNotFoundError


class Client:
    username: bytes
    password: bytes
    platform: Platform
    timeout: float
    track_steps: bool
    connection: Connection
    complete_steps: List[Step] = []

    def __init__(self, username: str, password: str, platform: Platform, timeout: float = 2.0,
                 track_steps: bool = True):
        self.username = username.encode('utf8')
        self.password = password.encode('utf8')
        self.platform = platform
        self.timeout = timeout
        self.track_steps = track_steps
        self.connection = Connection(FESL_DETAILS[self.platform]['host'], FESL_DETAILS[self.platform]['port'], timeout)

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        self.connection.close()

    def hello(self) -> bytes:
        if self.track_steps and Step.hello in self.complete_steps:
            return b''

        hello_packet = self.get_hello_packet()
        self.connection.write(hello_packet)
        self.complete_steps.append(Step.hello)
        return self.connection.read()

    def memcheck(self) -> bytes:
        if self.track_steps and Step.memcheck in self.complete_steps:
            return b''
        elif self.track_steps and Step.hello not in self.complete_steps:
            self.hello()

        memcheck_packet = self.get_memcheck_packet()
        self.connection.write(memcheck_packet)
        self.complete_steps.append(Step.memcheck)
        return self.connection.read()

    def login(self) -> bytes:
        if self.track_steps and Step.login in self.complete_steps:
            return b''
        elif self.track_steps and Step.memcheck not in self.complete_steps:
            self.memcheck()

        login_packet = self.build_login_packet(self.username, self.password)
        self.connection.write(login_packet)
        self.complete_steps.append(Step.login)
        return self.connection.read()

    def lookup_usernames(self, usernames: List[str], namespace: Namespace) -> List[dict]:
        if self.track_steps and Step.login not in self.complete_steps:
            self.login()

        lookup_packet = self.build_user_lookup_packet(usernames, namespace)
        self.connection.write(lookup_packet)
        response = self.connection.read()
        body = response[12:-1]

        return self.parse_list_response(body, b'userInfo.')

    def lookup_username(self, username: str, namespace: Namespace) -> dict:
        results = self.lookup_usernames([username], namespace)

        if len(results) == 0:
            raise PyBfbc2StatsNotFoundError('Name lookup did not return any results')

        return results.pop()

    def get_stats(self, userid: int) -> dict:
        if self.track_steps and Step.login not in self.complete_steps:
            self.login()

        # Send query in chunks
        chunk_packets = self.build_stats_query_packets(userid)
        for chunk_packet in chunk_packets:
            self.connection.write(chunk_packet)

        response = b''
        has_more_packets = True
        while has_more_packets:
            packet = self.connection.read()
            data = self.handle_stats_response_packet(packet)
            response += data
            if data[-1:] == b'\x00':
                has_more_packets = False

        parsed = self.parse_list_response(response, b'stats.')
        return self.dict_list_to_dict(parsed)

    @staticmethod
    def build_list_body(items: List[Union[bytes, Dict[bytes, bytes]]], prefix: bytes):
        # Convert item list to bytes following "prefix.index.key=value"-format
        item_list = []
        for index, item in enumerate(items):
            if isinstance(item, dict):
                for key, value in item.items():
                    dotted_elements = [prefix, str(index).encode('utf8'), key]
                    # byte dict with prefix: userInfo.0.userName=NoobKillah
                    item_list.append(Client.build_list_item(dotted_elements, value))
            else:
                # bytes with prefix only: keys.0=accuracy
                dotted_elements = [prefix, str(index).encode('utf8')]
                item_list.append(Client.build_list_item(dotted_elements, item))

        # Join list together, add list length indicator and return
        return b'\n'.join(item_list) + b'\n' + prefix + b'.[]=' + str(len(items)).encode('utf8')

    @staticmethod
    def build_list_item(dotted_elements: List[bytes], value: bytes) -> bytes:
        return b'.'.join(dotted_elements) + b'=' + value

    @staticmethod
    def build_packet(header: bytes, body: bytes):
        # Add header, packet length indicators, body and tail together
        packet = bytearray(header + b'\x00\x00\x00\x00' + body + b'\n\x00')

        # Update length indicators
        packet[8] = len(packet) >> 24
        packet[9] = len(packet) >> 16
        packet[10] = len(packet) >> 8
        packet[11] = len(packet) & 255

        return bytes(packet)

    def get_hello_packet(self) -> bytes:
        return Client.build_packet(
            b'fsys\xc0\x00\x00\x01',
            b'TXN=Hello\nclientString=' + FESL_DETAILS[self.platform]['clientString'] + b'\nsku=PC\nlocale=en_US\n'
            b'clientPlatform=PC\nclientVersion=2.0\nSDKVersion=5.1.2.0.0\nprotocolVersion=2.0\nfragmentSize=8096\n'
            b'clientType=server'
        )

    @staticmethod
    def get_memcheck_packet() -> bytes:
        return Client.build_packet(
            b'fsys\x80\x00\x00\x00',
            b'TXN=MemCheck\nresult='
        )

    @staticmethod
    def build_login_packet(username: bytes, password: bytes) -> bytes:
        return Client.build_packet(
            b'acct\xc0\x00\x00\x02',
            b'TXN=Login\nreturnEncryptedInfo=0\n'
            b'name=' + username + b'\npassword=' + password + b'\nmacAddr=$000000000000'
        )

    @staticmethod
    def build_user_lookup_packet(usernames: List[str], namespace: Namespace) -> bytes:
        user_dicts = [{b'userName': username.encode('utf8'), b'namespace': bytes(namespace)} for username in usernames]
        lookup_list = Client.build_list_body(user_dicts, b'userInfo')
        lookup_packet = Client.build_packet(
            b'acct\xc0\x00\x00\n',
            b'TXN=NuLookupUserInfo\n' + lookup_list
        )

        return lookup_packet

    @staticmethod
    def build_stats_query_packets(userid: int) -> List[bytes]:
        userid_bytes = str(userid).encode('utf8')
        key_list = Client.build_list_body(STATS_KEYS, b'keys')
        stats_query = b'TXN=GetStats\nowner=' + userid_bytes + b'\nownerType=1\nperiodId=0\nperiodPast=0\n' + key_list
        # Base64 encode query for transfer
        stats_query_b64 = b64encode(stats_query)
        # Determine available packet length (subtract already used by query metadata and size indicator)
        encoded_query_size = str(len(stats_query_b64))
        available_packet_length = BUFFER_SIZE - (25 + len(encoded_query_size))

        # URL encode/quote query
        stats_query_enc = quote_from_bytes(stats_query_b64).encode('utf8')

        # Split query into chunks and build packets around them
        chunk_packets = []
        for i in range(0, len(stats_query_enc), available_packet_length):
            query_chunk = stats_query_enc[i:i + available_packet_length]
            chunk_packet = Client.build_packet(
                b'rank\xf0\x00\x00\x0b',
                b'size=' + encoded_query_size.encode('utf8') + b'\ndata=' + query_chunk
            )
            chunk_packets.append(chunk_packet)

        return chunk_packets

    @staticmethod
    def parse_list_response(raw_response: bytes, entry_prefix: bytes) -> List[dict]:
        lines = raw_response.split(b'\n')
        # Assign lines to either data or meta lines
        meta_lines = []
        data_lines = []
        for line in lines:
            if line.startswith(entry_prefix) and b'.[]' not in line:
                # Append data line (without entry prefix)
                # So for userInfo.0.userId=226804555, only add 0.userId=226804555 (assuming prefix is userInfo.)
                data_lines.append(line[len(entry_prefix):])
            else:
                # Add meta data lines as is
                meta_lines.append(line)

        # Determine data entry count
        length_info = next(line for line in meta_lines if b'.[]' in line)
        entry_count = int(length_info.split(b'=').pop())
        # Init dict list
        datasets = [{} for i in range(0, entry_count)]
        for line in data_lines:
            # Split into keys and data and split into index and key
            # line format will something like: 0.userId=22680455
            elements = line.split(b'=')
            key_elements = elements[0].split(b'.')
            index = int(key_elements[0])
            key = key_elements[1].decode()
            value = elements[1].decode()
            # Add value to dict
            datasets[index][key] = value

        return datasets

    @staticmethod
    def handle_stats_response_packet(packet: bytes):
        body = packet[12:-1]
        lines = body.split(b'\n')

        # Check for errors
        if b'data=' not in body:
            error_code_line = next((line for line in lines if line.startswith(b'errorCode=')), b'')
            error_code = error_code_line.split(b'=').pop()
            if error_code == b'21':
                raise PyBfbc2StatsParameterError('FESL returned invalid parameter error')
            else:
                raise PyBfbc2StatsError('FESL returned invalid response')

        data_line = next(line for line in lines if line.startswith(b'data='))
        # URL decode/unquote and base64 decode data
        data = b64decode(unquote_to_bytes(data_line[5:]))

        return data

    @staticmethod
    def dict_list_to_dict(dict_list: List[dict]) -> dict:
        sorted_list = sorted(dict_list, key=lambda x: x['key'])
        return {entry['key']: entry['value'] for entry in sorted_list}
