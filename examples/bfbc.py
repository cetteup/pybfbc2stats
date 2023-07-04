from urllib.parse import quote

from pybfbc2stats import FeslClient, Platform, Namespace, SecureConnection
from pybfbc2stats.packet import FeslPacket


def main():
    with FeslClient('ea_account_name', 'ea_account_password', Platform.xbox360) as client:
        # We don't know the hostname of the Xbox 360 backend, but we can use the PS3 backend with an Xbox client string
        client.connection = SecureConnection(
            'bfbc-ps3.fesl.ea.com',
            18800,
            FeslPacket,
            client.connection.timeout
        )
        client.client_string = b'bfbc-360'

        quoted_name = quote('daddyo21252')
        # Bad Company uses different ("legacy") namespaces (XBL_SUB and PS3_SUB)
        persona = client.lookup_username(quoted_name, Namespace.XBL_SUB)
        stats = client.get_stats(int(persona['userId']), [b'games', b'wins', b'losses'])
        print(stats)


if __name__ == '__main__':
    main()
