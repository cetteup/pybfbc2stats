# pybfbc2stats

Python 🐍 library for retrieving statistics of Battlefield: Bad Company 2 players. Possible thanks to previous work by Luigi Auriemma and nemo.

## Features

- lookup players/personas by id or name on any platform
- search for players/personas by name on any platform (with wildcard support)
- retrieve all available statistics for players on PC/PS3
- retrieve player leaderboards on PC/PS3
- retrieve server list for PC/PS3
- retrieve individual game server's details for PC/PS3 (including player list)
- full support for async Python

## Installation

Simply install the package via pip.

```bash
$ pip install pybfbc2stats
```

## Usage

### TLS 1.0

The FESL backend only supports TSL 1.0. So, you can only use this library in an environment that allows Python to use TLS 1.0. The easiest and least intrusive way to enable TLS 1.0 support is to set an `OPENSSL_CONF` environment variable that contains the absolute path to the included `openssl.cnf`. On Linux, you can set it by running this in the project directory:

```bash
export OPENSSL_CONF=$(realpath openssl.cnf)
```
### Basic example

The following examples show how to find a player/persona by name and retrieve their stats using the default as well as the async client.

### Retrieve stats using the default FESL client

```python
from urllib.parse import quote

from pybfbc2stats import FeslClient, Platform, Namespace


def main():
    with FeslClient('ea_account_name', 'ea_account_password', Platform.pc) as client:
        quoted_name = quote('Krut0r')
        persona = client.lookup_username(quoted_name, Namespace.pc)
        stats = client.get_stats(int(persona['userId']))
        print(stats)


if __name__ == '__main__':
    main()
```

### Retrieve stats using the async FESL client

```python
import asyncio
from urllib.parse import quote

from pybfbc2stats import AsyncFeslClient, Platform, Namespace


async def main():
    async with AsyncFeslClient('ea_account_name', 'ea_account_password', Platform.pc) as client:
        quoted_name = quote('Krut0r')
        persona = await client.lookup_username(quoted_name, Namespace.pc)
        stats = await client.get_stats(int(persona['userId']))
        print(stats)


if __name__ == '__main__':
    asyncio.run(main())
```

### Retrieve the server list using the default theater client

```python
from pybfbc2stats import FeslClient, TheaterClient, Platform

def main():
    # First, get theater details and login key (lkey) from FESL
    with FeslClient('ea_account_name', 'ea_account_password', Platform.ps3) as feslClient:
        theater_hostname, theater_port = feslClient.get_theater_details()
        lkey = feslClient.get_lkey()
    
    # Now use the theater client to get the server list
    with TheaterClient(theater_hostname, theater_port, lkey, Platform.ps3) as theaterClient:
        lobbies = theaterClient.get_lobbies()
        servers = []
        for lobby in lobbies:
            lobby_servers = theaterClient.get_servers(int(lobby['LID']))
            servers.extend(lobby_servers)
        print(servers)

if __name__ == '__main__':
    main()
```

### Retrieve the server list using the async theater client

```python
import asyncio
from pybfbc2stats import AsyncFeslClient, AsyncTheaterClient, Platform

async def main():
    # First, get theater details and login key (lkey) from FESL
    async with AsyncFeslClient('ea_account_name', 'ea_account_password', Platform.ps3) as feslClient:
        theater_hostname, theater_port = await feslClient.get_theater_details()
        lkey = await feslClient.get_lkey()
    
    # Now use the theater client to get the server list
    async with AsyncTheaterClient(theater_hostname, theater_port, lkey, Platform.ps3) as theaterClient:
        lobbies = await theaterClient.get_lobbies()
        servers = []
        for lobby in lobbies:
            lobby_servers = await theaterClient.get_servers(int(lobby['LID']))
            servers.extend(lobby_servers)
        print(servers)

if __name__ == '__main__':
    asyncio.run(main())
```

### Client methods

Both the default and the async clients offer the same methods with the same signatures.

#### \[Async\]FeslClient(username, password, platform, timeout)

Create a new [Async]FeslClient instance.

**Note**: The account has to be valid for Bad Company 2. If your account does not work, you can create a new one using [ealist](https://aluigi.altervista.org/papers.htm#ealist): `.\ealist.exe -A -a [username] [password] bfbc2-pc` (the created account will work for all platforms).

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`username`     | str  | Required
`password`     | str  | Required
`platform`     | Platform | Required | One of: `Platform.pc`, `Platform.ps3` (Xbox 360 is not yet supported)
`timeout`      | float   | Optional  | How long to wait for data before raising a timeout exception (timeout is applied **per socket operation**, meaning the timeout is applied to each read from/write to the underlying connection to the FESL backend)

----

#### \[Async\]FeslClient.hello()

Send the initial "hello" packet to the FESL server.

---

#### \[Async\]FeslClient.memcheck()

Send the response to the FESL server's "memcheck" challenge.

----

#### \[Async\]FeslClient.login()

Send the login details to the FESL server.

----

#### \[Async\]FeslClient.get_lkey()

Get the login key (lkey) used to authenticate on theater backend.

----

#### \[Async\]FeslClient.get_theater_details()

Get the hostname and port of the theater backend for the client's platform.

----

#### \[Async\]FeslClient.lookup_usernames(usernames, namespace)

Lookup a list of **url encoded/quoted** usernames and return any matching personas (only exact name matches are returned).

**Note**: Since this method accepts a `namespace` argument, it can lookup usernames in any namespace (on any platform), regardless of which `Platform` was used to create the client instance.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`usernames`     | List[str]  | Required | List of **url encoded/quoted** usernames
`namespace`     | Namespace | Required | One of: `Namespace.pc`, `Namespace.ps3`, `Namespace.xbox360`

**Example**

```python
from urllib.parse import quote

from pybfbc2stats import FeslClient, Platform, Namespace

client = FeslClient('ea_account_name', 'ea_account_password', Platform.pc)
names = ['SickLittleMonkey', '[SuX] DeLuXe']
quoted = [quote(name) for name in names]
persona = client.lookup_usernames(quoted, Namespace.pc)
```

----

#### \[Async\]FeslClient.lookup_username(username, namespace)

Lookup a single **url encoded/quoted** username and return any matching persona (only exact name matches are returned).

**Note**: Since this method accepts a `namespace` argument, it can lookup usernames in any namespace (on any platform), regardless of which `Platform` was used to create the client instance.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`username`     | str  | Required | **Url encoded/quoted** username
`namespace`     | Namespace | Required | One of: `Namespace.pc`, `Namespace.ps3`, `Namespace.xbox360`

**Example**

```python
from urllib.parse import quote

from pybfbc2stats import FeslClient, Platform, Namespace

client = FeslClient('ea_account_name', 'ea_account_password', Platform.ps3)
persona = client.lookup_username(quote('Major Brainhurt'), Namespace.pc)
```

----

#### \[Async\]FeslClient.lookup_user_ids(user_ids, namespace)

Lookup a list of user ids and return any matching personas.

**Note**: Since this method accepts a `namespace` argument, it can lookup user ids in any namespace (on any platform), regardless of which `Platform` was used to create the client instance.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`user_ids`     | List[int]  | Required | 
`namespace`     | Namespace | Required | One of: `Namespace.pc`, `Namespace.ps3`, `Namespace.xbox360`

**Example**

```python
from pybfbc2stats import FeslClient, Platform, Namespace

client = FeslClient('ea_account_name', 'ea_account_password', Platform.pc)
persona = client.lookup_user_ids([232302860, 233866102], Namespace.xbox360)
```

----

#### \[Async\]FeslClient.lookup_user_id(user_id, namespace)

Lookup a single user id and return any matching persona.

**Note**: Since this method accepts a `namespace` argument, it can lookup user ids in any namespace (on any platform), regardless of which `Platform` was used to create the client instance.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`user_id`     | int  | Required | 
`namespace`     | Namespace | Required | One of: `Namespace.pc`, `Namespace.ps3`, `Namespace.xbox360`

**Example**

```python
from pybfbc2stats import FeslClient, Platform, Namespace

client = FeslClient('ea_account_name', 'ea_account_password', Platform.pc)
persona = client.lookup_user_id(232302860, Namespace.xbox360)
```

----

#### \[Async\]FeslClient.search_name(screen_name, namespace)

Find personas given a **url encoded/quoted** (partial) name. You can use `*` as a trailing wildcard.

**Note**: The FESL backend returns an error both if a) no matching results were found and b) too many matching results were found. So, be careful with wildcard characters in combination with short partial names.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`screen_name`     | str  | Required | **Url encoded/quoted** (partial) name
`namespace`     | Namespace | Required | One of: `Namespace.pc`, `Namespace.ps3`, `Namespace.xbox360`

**Example**

```python
from urllib.parse import quote

from pybfbc2stats import FeslClient, Platform

client = FeslClient('ea_account_name', 'ea_account_password', Platform.pc)
results = client.search_name(quote('[=BL=] larryp11'))
```

----

#### \[Async\]FeslClient.get_stats(userid, keys)

Retrieve a given list of stats attributes for a given player id on the client instance's platform.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`userid`       | int  | Required | 
`keys`         | List[bytes] | Optional | By default, all available attributes are retrieved (see `STATS_KEYS` constant for details)

**Example**

```python
from pybfbc2stats import FeslClient, Platform

client = FeslClient('ea_account_name', 'ea_account_password', Platform.ps3)
stats = client.get_stats(223789857, [b'accuracy', b'kills', b'deaths', b'score', b'time'])
```

----

#### \[Async\]FeslClient.get_leaderboard(min_rank, max_rank, sort_by, keys)

Retrieve a given range of players on the leaderboard with the given list of stats, sorted by a given key, on the client instance's platform.

**Note**: There does not seem to be a hard limit to either the rank rage size nor the number of stats keys that can be retrieved for each player. You will, however, need to increase your client-wide timeout if you are planning to retrieve large chunks of the leaderboard or lots of stats attributes.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`min_rank`       | int  | Optional | Minimum placement/rank on the leaderboard (1-250000)
`max_rank`       | int  | Optional | Maximum placement/rank on the leaderboard (1-250001)
`sort_by`      | bytes | Optional  | Key to sort leaderboard by, must be one of `deaths`, `elo`, `kills`, `rank`, `score`, `time`, `veteran`
`keys`         | List[bytes] | Optional | By default, only `deaths`, `kills`, `score` and `time` are retrieved (see `STATS_KEYS` constant for additional available keys)

**Example**

```python
from pybfbc2stats import FeslClient, Platform

client = FeslClient('ea_account_name', 'ea_account_password', Platform.pc)
leaderboard = client.get_leaderboard(1, 50, b'time')
```

----

#### \[Async\]TheaterClient(host, port, lkey, platform, timeout)

Create a new [Async]TheaterClient instance.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`host`         | str  | Required     | IP/hostname of the theater backend for the platform (can be retrieved via FESL)
`port`         | int  | Required     | Port of the theater backend for the platform (can be retrieved via FESL)
`lkey`         | str  | Required     | Login key (lkey) (retrieved via FESL)
`platform`     | Platform | Required | One of: `Platform.pc`, `Platform.ps3` (Xbox 360 is not yet supported)
`timeout`      | float   | Optional  | How long to wait for data before raising a timeout exception (timeout is applied **per socket operation**, meaning the timeout is applied to each read from/write to the underlying connection to the FESL backend)

----

#### \[Async\]TheaterClient.connect()

Initialize the connection to the Theater backend by sending the initial CONN/hello packet.

----

#### \[Async\]TheaterClient.authenticate()

Authenticate against/log into the Theater backend using the lkey retrieved via FESL.

----

#### \[Async\]TheaterClient.get_lobbies()

Retrieve all available game (server) lobbies.

**Example**

```python
from pybfbc2stats import TheaterClient, Platform

client = TheaterClient('bfbc2-ps3-server.theater.ea.com', 18336, 'your_lkey', Platform.ps3)
lobbies = client.get_lobbies()
```

----

#### \[Async\]TheaterClient.get_servers(lobby_id)

Retrieve all available game servers from the given lobby.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
lobby_id       | int  | Required     | Id of the game server lobby

**Example**

```python
from pybfbc2stats import TheaterClient, Platform

client = TheaterClient('bfbc2-ps3-server.theater.ea.com', 18336, 'your_lkey', Platform.ps3)
servers = client.get_servers(257)
```

----

#### \[Async\]TheaterClient.get_server_details(lobby_id, game_id)

Retrieve full details and player list for a given server.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
lobby_id       | int  | Required     | If of the game server lobby the server is hosted in
game_id        | int  | Required     | Game (server) id

**Example**

```python
from pybfbc2stats import TheaterClient, Platform

client = TheaterClient('bfbc2-ps3-server.theater.ea.com', 18336, 'your_lkey', Platform.ps3)
general, detailed, players = client.get_server_details(257, 120018)
```
