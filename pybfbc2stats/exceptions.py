class PyBfbc2StatsError(Exception):
    pass


class PyBfbc2StatsTimeoutError(PyBfbc2StatsError):
    pass


class PyBfbc2ParameterError(PyBfbc2StatsError):
    pass
