from .asyncio_client import AsyncClient
from .asyncio_connection import AsyncConnection
from .client import Client
from .connection import Connection
from .constants import Platform, Namespace, DEFAULT_LEADERBOARD_KEYS, STATS_KEYS
from .exceptions import PyBfbc2StatsError, PyBfbc2StatsTimeoutError, PyBfbc2StatsParameterError, \
    PyBfbc2StatsNotFoundError, PyBfbc2StatsLoginError, PyBfbc2StatsConnectionError, PyBfbc2StatsSearchError

"""
pybfbc2stats.
Simple Python library for retrieving statistics of Battlefield: Bad Company 2 players.
"""

__version__ = '0.2.8'
__author__ = 'cetteup'
__credits__ = 'nemo, Luigi Auriemma'
__all__ = ['Connection', 'Client', 'AsyncConnection', 'AsyncClient',
           'Platform', 'Namespace', 'DEFAULT_LEADERBOARD_KEYS', 'STATS_KEYS',
           'PyBfbc2StatsError', 'PyBfbc2StatsConnectionError', 'PyBfbc2StatsParameterError', 'PyBfbc2StatsTimeoutError',
           'PyBfbc2StatsLoginError', 'PyBfbc2StatsNotFoundError', 'PyBfbc2StatsSearchError']
