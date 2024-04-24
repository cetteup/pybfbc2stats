from typing import Optional, List, Union, Tuple

from .asyncio_client import AsyncFeslClient, AsyncTheaterClient
from .asyncio_connection import AsyncConnection
from .client import FeslClient, TheaterClient
from .connection import Connection
from .constants import Platform, Backend, FeslTransmissionType, FeslStep, LookupType, Namespace, STATS_KEYS, \
    DEFAULT_LEADERBOARD_KEYS
from .exceptions import NotImplementedError, Error, ServerNotFoundError, PlayerNotFoundError, LobbyNotFoundError
from .packet import FeslPacket
from .payload import StrValue, Payload, IntValue


class RomeFeslClient(FeslClient):
    connection: Connection

    def __init__(self, email: str, password: str, timeout: float = 3.0, track_steps: bool = True):
        host, port, client_string = self.get_backend_details(Backend.rome, Platform.pc)
        # Rome does not support SSL => use a Connection without it
        connection = Connection(host, port, FeslPacket, timeout)
        # "Skip" FeslClient constructor, for details see note in AsyncFeslClient.__init__
        super(FeslClient, self).__init__(connection, Platform.pc, client_string, timeout, track_steps)
        # Rome uses the email-based NuLogin, constructor parameter "email" is just called that to make it obvious
        self.username = email.encode('utf8')
        self.password = password.encode('utf8')

    def login(self, tos_version: Optional[StrValue] = None) -> bytes:
        super().login(tos_version)
        # Rome requires a persona to be logged in, account login is not sufficient
        return self.login_persona()

    def logout(self) -> Optional[bytes]:
        # Only send logout if client is currently logged in
        if self.completed_step(FeslStep.login) or self.completed_step(FeslStep.login_persona):
            tid = self.get_transaction_id()
            logout_packet = self.build_logout_packet(tid)
            self.connection.write(logout_packet)
            self.completed_steps.clear()
            # Rome does not respond to logout packets, skip the read here
            return

    def get_lkey(self) -> str:
        if not self.completed_step(FeslStep.login_persona):
            self.login_persona()

        # Use the lkey from the persona login instead of the account login
        packet = self.completed_steps[FeslStep.login_persona]
        payload = packet.get_payload()

        return payload.get_str('lkey', str())

    def lookup_user_identifiers(self, identifiers: List[Union[StrValue, IntValue]], namespace: Namespace,
                                lookup_type: LookupType) -> List[dict]:
        raise NotImplementedError('Looking up players by name/id is not implemented on Project Rome')

    def search_name(self, screen_name: StrValue, namespace: Namespace) -> dict:
        raise NotImplementedError('Searching players by name is not implemented on Project Rome')

    def get_stats(self, userid: IntValue, keys: List[StrValue] = STATS_KEYS) -> dict:
        raise NotImplementedError('Fetching stats of (other) players is not implemented on Project Rome')

    def get_leaderboard(self, min_rank: IntValue = 1, max_rank: IntValue = 50, sort_by: StrValue = 'score',
                        keys: List[StrValue] = DEFAULT_LEADERBOARD_KEYS) -> List[dict]:
        raise NotImplementedError('Leaderboards are not implemented on Project Rome')

    def get_dogtags(self, userid: IntValue) -> List[dict]:
        raise NotImplementedError('Fetching dogtags of (other) players is not implemented on Project Rome')

    @staticmethod
    def build_login_packet(tid: int, username: StrValue, password: StrValue, tos_version: Optional[StrValue] = None) -> FeslPacket:
        return FeslPacket.build(
            b'acct',
            Payload(
                TXN='NuLogin',
                returnEncryptedInfo=0,
                nuid=username,
                password=password,
                macAddr='$000000000000',
                tosVersion=tos_version
            ),
            FeslTransmissionType.SinglePacketRequest,
            tid
        )


class AsyncRomeFeslClient(AsyncFeslClient, RomeFeslClient):
    connection: AsyncConnection

    def __init__(self, username: str, password: str, timeout: float = 3.0, track_steps: bool = True):
        host, port, client_string = self.get_backend_details(Backend.rome, Platform.pc)
        connection = AsyncConnection(host, port, FeslPacket, timeout)
        """
        Multiple inheritance works here, but only if we "skip" the FeslClient constructor. The method resolution here
        is: AsyncNexusFeslClient, AsyncFeslClient, NexusFeslClient, FeslClient, AsyncClient, Client. So, by calling 
        super(), we would call the AsyncFeslClient __init__ function with parameters that make no sense. If we instead 
        use super(FeslClient, self), we call FeslClient's super directly - effectively skipping the AsyncFeslClient, 
        NexusFeslClient and FeslClient constructor
        """
        super(FeslClient, self).__init__(connection, Platform.pc, client_string, timeout, track_steps)
        self.username = username.encode('utf8')
        self.password = password.encode('utf8')

    async def login(self, tos_version: Optional[StrValue] = None) -> bytes:
        await super().login(tos_version)
        # Rome requires a persona to be logged in, account login is not sufficient
        return await self.login_persona()

    async def logout(self) -> Optional[bytes]:
        # Only send logout if client is currently logged in
        if self.completed_step(FeslStep.login) or self.completed_step(FeslStep.login_persona):
            tid = self.get_transaction_id()
            logout_packet = self.build_logout_packet(tid)
            await self.connection.write(logout_packet)
            self.completed_steps.clear()
            # Rome does not respond to logout packets, skip read here
            return

    async def get_lkey(self) -> str:
        if not self.completed_step(FeslStep.login_persona):
            await self.login_persona()

        # Use the lkey from the persona login instead of the account login
        packet = self.completed_steps[FeslStep.login_persona]
        payload = packet.get_payload()

        return payload.get_str('lkey', str())

    async def lookup_user_identifiers(self, identifiers: List[Union[StrValue, IntValue]], namespace: Namespace,
                                lookup_type: LookupType) -> List[dict]:
        raise NotImplementedError('Looking up players by name/id is not implemented on Project Rome')

    async def search_name(self, screen_name: StrValue, namespace: Namespace) -> dict:
        raise NotImplementedError('Searching players by name is not implemented on Project Rome')

    async def get_stats(self, userid: IntValue, keys: List[StrValue] = STATS_KEYS) -> dict:
        raise NotImplementedError('Fetching stats of (other) players is not implemented on Project Rome')

    async def get_leaderboard(self, min_rank: IntValue = 1, max_rank: IntValue = 50, sort_by: StrValue = 'score',
                        keys: List[StrValue] = DEFAULT_LEADERBOARD_KEYS) -> List[dict]:
        raise NotImplementedError('Leaderboards are not implemented on Project Rome')

    async def get_dogtags(self, userid: IntValue) -> List[dict]:
        raise NotImplementedError('Fetching dogtags of (other) players is not implemented on Project Rome')


class RomeTheaterClient(TheaterClient):
    def __init__(self, host: str, port: int, lkey: StrValue, timeout: float = 3.0, track_steps: bool = True):
        super().__init__(host, port, lkey, Platform.pc, timeout, track_steps)

    def get_servers(self, lobby_id: IntValue) -> List[dict]:
        servers = super().get_servers(lobby_id)
        is_error, error = self.is_glst_error_response(servers, lobby_id)
        if is_error:
            raise error

        return servers

    def get_current_server(self, user_id: IntValue) -> Tuple[dict, dict, List[dict]]:
        raise NotImplementedError('Fetching the current server of players is not implemented on Project Rome')

    def get_gdat(self, **kwargs: IntValue) -> Tuple[dict, dict, List[dict]]:
        gdat, gdet, players = super().get_gdat(**kwargs)
        is_error, error = self.is_gdat_error_response(gdat, **kwargs)
        if is_error:
            raise error

        return gdat, gdet, players

    @staticmethod
    def is_glst_error_response(servers: List[dict], lobby_id: int) -> Tuple[bool, Optional[Error]]:
        # Project Rome returns the same server list regardless of the given LID
        # Since it sends a valid GLST packet and all GDAT packets, we need to check for errors after reading every packet
        # If we just changed TheaterClient.is_error_response, we would leave unread garbage on the connection
        for server in servers:
            if server.get('LID') != lobby_id:
                # Server LID does not match, mimic GLSTnrom
                return True, LobbyNotFoundError('Theater returned lobby not found error')

        return False, None

    @staticmethod
    def is_gdat_error_response(gdat: dict, **kwargs: IntValue) -> Tuple[bool, Optional[Error]]:
        # Project Rome theater returns "empty" GDAT and GDET responses instead of an error response
        # Since it sends both a "valid" GDAT and GDET packet, we need to check for errors after reading both
        # If we just changed TheaterClient.is_error_response, we would leave unread garbage on the connection
        if 'LID' not in gdat and 'LID' in kwargs:
            # Server specified by LID (and GID) not found, mimic GDATngam behavior
            return True, ServerNotFoundError('Theater returned server not found error')
        elif 'LID' in kwargs and gdat.get('LID') != kwargs['LID']:
            # Server found but LID does not match (Rome returns the same server list regardless of the given LID)
            return True, ServerNotFoundError('Theater returned server not found error')
        elif 'LID' not in gdat and 'UID' in kwargs:
            # Server specified by UID not found, mimic GDATntfn behavior
            return True, PlayerNotFoundError('Theater returned player not found/not online error')

        return False, None


class AsyncRomeTheaterClient(AsyncTheaterClient, RomeTheaterClient):
    def __init__(self, host: str, port: int, lkey: StrValue, timeout: float = 3.0, track_steps: bool = True):
        super().__init__(host, port, lkey, Platform.pc, timeout, track_steps)

    async def get_servers(self, lobby_id: IntValue) -> List[dict]:
        servers = await super().get_servers(lobby_id)
        is_error, error = self.is_glst_error_response(servers, lobby_id)
        if is_error:
            raise error

        return servers

    async def get_current_server(self, user_id: IntValue) -> Tuple[dict, dict, List[dict]]:
        raise NotImplementedError('Fetching the current server of players is not implemented on Project Rome')

    async def get_gdat(self, **kwargs: IntValue) -> Tuple[dict, dict, List[dict]]:
        gdat, gdet, players = await super().get_gdat(**kwargs)
        is_error, error = self.is_gdat_error_response(gdat, **kwargs)
        if is_error:
            raise error

        return gdat, gdet, players
