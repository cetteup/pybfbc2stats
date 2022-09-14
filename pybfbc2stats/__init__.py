from .asyncio_client import AsyncFeslClient, AsyncTheaterClient
from .asyncio_connection import AsyncConnection, AsyncSecureConnection
from .client import FeslClient, TheaterClient
from .connection import Connection, SecureConnection
from .constants import Platform, Namespace, DEFAULT_LEADERBOARD_KEYS, STATS_KEYS
from .exceptions import Error, TimeoutError, ParameterError, \
    PlayerNotFoundError, AuthError, ConnectionError, SearchError, \
    NotFoundError, ServerNotFoundError, LobbyNotFoundError

"""
pybfbc2stats.
Python library for retrieving statistics of Battlefield: Bad Company 2 players.
"""

__version__ = '0.3.8'
__author__ = 'cetteup'
__credits__ = 'nemo, Luigi Auriemma'
__all__ = ['Connection', 'SecureConnection', 'FeslClient', 'TheaterClient',
           'AsyncConnection', 'AsyncSecureConnection', 'AsyncFeslClient', 'AsyncTheaterClient',
           'Platform', 'Namespace', 'DEFAULT_LEADERBOARD_KEYS', 'STATS_KEYS',
           'Error', 'ConnectionError', 'ParameterError', 'TimeoutError',
           'AuthError', 'NotFoundError', 'PlayerNotFoundError',
           'ServerNotFoundError', 'LobbyNotFoundError', 'SearchError']
