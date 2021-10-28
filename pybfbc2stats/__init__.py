from .asyncio_client import AsyncClient
from .asyncio_connection import AsyncConnection
from .client import Client
from .connection import Connection
from .constants import Platform, Namespace
from .exceptions import PyBfbc2StatsError, PyBfbc2StatsTimeoutError, PyBfbc2StatsParameterError, \
    PyBfbc2StatsNotFoundError

"""
pybfbc2stats.
Simple Python library for retrieving statistics of Battlefield: Bad Company 2 players.
"""

__version__ = '0.1.5'
__author__ = 'cetteup'
__credits__ = 'nemo, Luigi Auriemma'
__all__ = ['Connection', 'Client', 'AsyncConnection', 'AsyncClient', 'PyBfbc2StatsError', 'Platform', 'Namespace',
           'PyBfbc2StatsParameterError', 'PyBfbc2StatsTimeoutError', 'PyBfbc2StatsNotFoundError']
