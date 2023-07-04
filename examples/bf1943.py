from urllib.parse import quote

from pybfbc2stats import FeslClient, Platform, Namespace, SecureConnection
from pybfbc2stats.packet import FeslPacket


def main():
    with FeslClient('ea_account_name', 'ea_account_password', Platform.ps3) as client:
        # Override the connection to connect to the Battlefield 1943 backend
        client.connection = SecureConnection(
            'beach-ps3-server.fesl.ea.com',
            18331,
            FeslPacket,
            client.connection.timeout
        )
        client.client_string = b'beach-ps3'

        quoted_name = quote('sam707')
        persona = client.lookup_username(quoted_name, Namespace.ps3)
        stats = client.get_stats(int(persona['userId']), [b'games', b'wins', b'losses'])
        print(stats)


if __name__ == '__main__':
    main()
