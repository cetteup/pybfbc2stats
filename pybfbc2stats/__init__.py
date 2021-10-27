from .connection import Connection
from .client import Client
from .exceptions import PyBfbc2StatsError, PyBfbc2StatsTimeoutError, PyBfbc2StatsParameterError, \
    PyBfbc2StatsNotFoundError

"""
pybfbc2stats.
Simple Python library for retrieving statistics of Battlefield: Bad Company 2 players.
"""

__version__ = '0.1.3'
__author__ = 'cetteup'
__credits__ = 'nemo, Luigi Auriemma'
__all__ = ['Connection', 'Client', 'PyBfbc2StatsError', 'PyBfbc2StatsParameterError', 'PyBfbc2StatsTimeoutError',
           'PyBfbc2StatsNotFoundError']
