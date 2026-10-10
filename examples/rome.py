from pybfbc2stats import Platform, RomeFeslClient, RomeTheaterClient


def main():
    with RomeFeslClient('vu_account_email@example.com', 'vu_account_password', Platform.pc) as fesl:
        with RomeTheaterClient(*fesl.get_theater_details(), fesl.get_lkey(), Platform.pc) as theater:
            for lobby in theater.get_lobbies():
                for server in theater.get_servers(int(lobby['LID'])):
                    print(server['N'])


if __name__ == '__main__':
    main()
