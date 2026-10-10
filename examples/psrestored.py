from urllib.parse import quote

from pybfbc2stats import Platform, FeslClient, Namespace, SecureConnection
from pybfbc2stats.packet import FeslPacket


def main():
    with FeslClient('ea_account_name', 'ea_account_password', Platform.ps3) as client:
        client.connection = SecureConnection(
            'fesl.psrestored.online',
            18121,
            FeslPacket,
            client.connection.timeout
        )

        quoted_name = quote('lilboogiemannn')
        persona = client.lookup_username(quoted_name, Namespace.ps3)
        stats = client.get_stats(int(persona['userId']), [b'games', b'wins', b'losses'])
        print(stats)


if __name__ == '__main__':
    main()
