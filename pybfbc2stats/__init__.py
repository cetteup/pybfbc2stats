from .asyncio_client import AsyncFeslClient, AsyncTheaterClient
from .asyncio_connection import AsyncConnection, AsyncSecureConnection
from .client import FeslClient, TheaterClient
from .connection import Connection, SecureConnection
from .constants import Platform, Namespace, DEFAULT_LEADERBOARD_KEYS, STATS_KEYS
from .exceptions import PyBfbc2StatsError, PyBfbc2StatsTimeoutError, PyBfbc2StatsParameterError, \
    PyBfbc2StatsNotFoundError, PyBfbc2StatsAuthError, PyBfbc2StatsConnectionError, PyBfbc2StatsSearchError

"""
pybfbc2stats.
Simple Python library for retrieving statistics of Battlefield: Bad Company 2 players.
"""

__version__ = '0.3.0'
__author__ = 'cetteup'
__credits__ = 'nemo, Luigi Auriemma'
__all__ = ['Connection', 'SecureConnection', 'FeslClient', 'TheaterClient',
           'AsyncConnection', 'AsyncSecureConnection', 'AsyncFeslClient', 'AsyncTheaterClient',
           'Platform', 'Namespace', 'DEFAULT_LEADERBOARD_KEYS', 'STATS_KEYS',
           'PyBfbc2StatsError', 'PyBfbc2StatsConnectionError', 'PyBfbc2StatsParameterError', 'PyBfbc2StatsTimeoutError',
           'PyBfbc2StatsAuthError', 'PyBfbc2StatsNotFoundError', 'PyBfbc2StatsSearchError']
