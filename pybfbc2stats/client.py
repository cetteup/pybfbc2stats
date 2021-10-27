from base64 import b64encode, b64decode
from enum import Enum
from typing import List
from urllib.parse import quote_from_bytes, unquote_to_bytes

from .connection import Connection
from .constants import STATS_KEYS, BUFFER_SIZE
from .exceptions import PyBfbc2StatsParameterError, PyBfbc2StatsError, PyBfbc2StatsNotFoundError


class Step(int, Enum):
    hello = 1
    memcheck = 2
    login = 3


class Client:
    __username: bytes
    __password: bytes
    __timeout: float
    __connection: Connection
    __complete_steps: List[Step] = []

    def __init__(self, username: str, password: str, timeout: float = 2.0):
        self.__username = username.encode('utf8')
        self.__password = password.encode('utf8')
        self.__timeout = timeout
        self.__connection = Connection('bfbc2-pc-server.fesl.ea.com', 18321, timeout)

    def hello(self) -> bytes:
        if Step.hello in self.__complete_steps:
            return b''

        hello_packet = self.__build_packet(
            b'fsys\xc0\x00\x00\x01\x00\x00\x00\xb2',
            b'TXN=Hello\nclientString=bfbc2-pc\nsku=PC\nlocale=en_US\nclientPlatform=PC\nclientVersion=2.0\n'
            b'SDKVersion=5.1.2.0.0\nprotocolVersion=2.0\nfragmentSize=8096\nclientType=server'
        )
        self.__connection.write(hello_packet)
        self.__complete_steps.append(Step.hello)
        return self.__connection.read()

    def memcheck(self) -> bytes:
        if Step.memcheck in self.__complete_steps:
            return b''
        elif Step.hello not in self.__complete_steps:
            self.hello()

        memcheck_packet = self.__build_packet(
            b'fsys\x80\x00\x00\x00\x00\x00\x00"',
            b'TXN=MemCheck\nresult='
        )
        self.__connection.write(memcheck_packet)
        self.__complete_steps.append(Step.memcheck)
        return self.__connection.read()

    def login(self) -> bytes:
        if Step.login in self.__complete_steps:
            return b''
        elif Step.memcheck not in self.__complete_steps:
            self.memcheck()

        login_packet = self.__build_packet(
            b'acct\xc0\x00\x00\x02\x00\x00\x00s',
            b'TXN=NuLogin\nreturnEncryptedInfo=0\n'
            b'nuid=' + self.__username + b'\npassword=' + self.__password + b'\nmacAddr=$000000000000'
        )
        self.__connection.write(login_packet)
        self.__complete_steps.append(Step.login)
        return self.__connection.read()

    def lookup_usernames(self, usernames: List[str]) -> List[dict]:
        if Step.login not in self.__complete_steps:
            self.login()

        usernames_bytes = [username.encode('utf8') for username in usernames]
        lookup_list = self.__build_list_body(usernames_bytes, b'userInfo.', b'.userName')
        lookup_bytearray = bytearray(self.__build_packet(
            b'acct\xc0\x00\x00\n\x00\x00\x00K',
            b'TXN=NuLookupUserInfo\n' + lookup_list
        ))

        # Shift some bytes
        lookup_bytearray[8] = len(lookup_bytearray) >> 24
        lookup_bytearray[9] = len(lookup_bytearray) >> 16
        lookup_bytearray[10] = len(lookup_bytearray) >> 8
        lookup_bytearray[11] = len(lookup_bytearray) & 255

        lookup_packet = bytes(lookup_bytearray)
        self.__connection.write(lookup_packet)
        response = self.__connection.read()
        body = response[12:-1]

        return self.parse_list_response(body, b'userInfo.')

    def lookup_username(self, username: str) -> dict:
        results = self.lookup_usernames([username])

        if len(results) == 0:
            raise PyBfbc2StatsNotFoundError('Name lookup did not return any results')

        return results.pop()

    def get_stats(self, userid: int) -> dict:
        if Step.login not in self.__complete_steps:
            self.login()

        userid_bytes = str(userid).encode('utf8')
        key_list = self.__build_list_body(STATS_KEYS, b'keys.')
        stats_query = b'TXN=GetStats\nowner=' + userid_bytes + b'\nownerType=1\nperiodId=0\nperiodPast=0\n' + key_list
        # Base64 encode query for transfer
        stats_query_b64 = b64encode(stats_query)
        # Determine available packet length (subtract already used by query metadata and size indicator)
        encoded_query_size = str(len(stats_query_b64))
        available_packet_length = BUFFER_SIZE - (25 + len(encoded_query_size))

        # URL encode/quote query
        stats_query_enc = quote_from_bytes(stats_query_b64).encode('utf8')

        # Send query in chunks
        for i in range(0, len(stats_query_enc), available_packet_length):
            query_chunk = stats_query_enc[i:i + available_packet_length]
            chunk_bytearray = bytearray(self.__build_packet(
                b'rank\xf0\x00\x00\x0b\x00\x00\x1f\x9e',
                b'size=' + encoded_query_size.encode('utf8') + b'\ndata=' + query_chunk
            ))
            # Shift some bytes
            chunk_bytearray[10] = len(chunk_bytearray) >> 8
            # "Truncate" length to one byte
            chunk_bytearray[11] = len(chunk_bytearray) & 255
            chunk_packet = bytes(chunk_bytearray)
            self.__connection.write(chunk_packet)

        response = b''
        has_more_packets = True
        while has_more_packets:
            packet = self.__connection.read()
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
            response += data
            if data[-1:] == b'\x00':
                has_more_packets = False

        return {entry['key']: entry['value'] for entry in self.parse_list_response(response, b'stats.')}

    @staticmethod
    def __build_list_body(items: List[bytes], prefix: bytes, key: bytes = b''):
        # Convert item list to bytes following "prefix.index.key=value"-format (userInfo.0.userName=NoobKillah)
        item_list = [prefix + str(index).encode('utf8') + key + b'=' + value for (index, value) in enumerate(items)]

        # Join list together, add list length indicator and return
        return b'\n'.join(item_list) + b'\n' + prefix + b'[]=' + str(len(items)).encode('utf8')

    @staticmethod
    def __build_packet(header: bytes, body: bytes):
        return header + body + b'\n\x00'

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
