class PyBfbc2StatsError(Exception):
    pass


class PyBfbc2StatsTimeoutError(PyBfbc2StatsError):
    pass


class PyBfbc2StatsParameterError(PyBfbc2StatsError):
    pass


class PyBfbc2StatsNotFoundError(PyBfbc2StatsError):
    pass
