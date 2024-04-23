from typing import Optional, List, Union, Tuple

from .asyncio_client import AsyncFeslClient, AsyncTheaterClient
from .asyncio_connection import AsyncConnection
from .client import FeslClient, TheaterClient
from .connection import Connection
from .constants import Platform, Backend, FeslTransmissionType, FeslStep, LookupType, Namespace, STATS_KEYS, \
    DEFAULT_LEADERBOARD_KEYS
from .exceptions import NotImplementedError
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

    def get_current_server(self, user_id: IntValue) -> Tuple[dict, dict, List[dict]]:
        raise NotImplementedError('Fetching the current server of players is not implemented on Project Rome')


class AsyncRomeTheaterClient(AsyncTheaterClient, RomeTheaterClient):
    def __init__(self, host: str, port: int, lkey: StrValue, timeout: float = 3.0, track_steps: bool = True):
        super().__init__(host, port, lkey, Platform.pc, timeout, track_steps)

    async def get_current_server(self, user_id: IntValue) -> Tuple[dict, dict, List[dict]]:
        raise NotImplementedError('Fetching the current server of players is not implemented on Project Rome')
