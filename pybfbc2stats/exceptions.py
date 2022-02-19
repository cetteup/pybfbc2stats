class Error(Exception):
    pass


class ConnectionError(Error):
    pass


class TimeoutError(Error):
    pass


class AuthError(Error):
    pass


class ParameterError(Error):
    pass


class NotFoundError(Error):
    pass


class PlayerNotFoundError(NotFoundError):
    pass


class LobbyNotFoundError(NotFoundError):
    pass


class ServerNotFoundError(NotFoundError):
    pass


class SearchError(Error):
    pass
