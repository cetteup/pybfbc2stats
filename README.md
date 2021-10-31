# pybfbc2stats

Simple Python 🐍 library for retrieving statistics of Battlefield: Bad Company 2 players. Possible thanks to previous work by Luigi Auriemma and nemo.

## Features

- lookup players/personas by id or name on any platform
- search for players/personas by name on PC/PS3 (with wildcard support)
- retrieve all available statistics for players on PC/PS3
- retrieve player leaderboards on PC/PS3
- full support for async Python

## Installation

Simply install the package via pip.

```bash
$ pip install pybfbc2stats
```

## Usage

### Basic example

The following examples show how to find a player/persona by name and retrieve their stats using the default as well as the async client.

### Retrieve stats using the default client

```python
from urllib.parse import quote

from pybfbc2stats import Client, Platform, Namespace


async def main():
    with Client('ea_account_name', 'ea_account_password', Platform.pc) as client:
        quoted_name = quote('Krut0r')
        persona = client.lookup_username(quoted_name, Namespace.pc)
        stats = client.get_stats(int(persona['userId']))
        print(stats)

if __name__ == '__main__':
    main()
```

### Retrieve stats using the async client

```python
import asyncio
from urllib.parse import quote

from pybfbc2stats import AsyncClient, Platform, Namespace


async def main():
    async with AsyncClient('ea_account_name', 'ea_account_password', Platform.pc) as client:       
        quoted_name = quote('Krut0r')
        persona = await client.lookup_username(quoted_name, Namespace.pc)
        stats = await client.get_stats(int(persona['userId']))
        print(stats)

if __name__ == '__main__':
    asyncio.run(main())
```

### Client methods

Both the default and the async clients offer the same methods with the same signatures.

#### \[Async\]Client(username, password, platform, timeout)

Create a new [Async]Client instance.

**Note**: The account has to be valid for Bad Company 2. If your account does not work, you can create a new one using [ealist](https://aluigi.altervista.org/papers.htm#ealist): `.\ealist.exe -A -a [username] [password] bfbc2-pc` (the created account will work for all platforms).

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`username`     | str  | Required
`password`     | str  | Required
`platform`     | Platform | Required | One of: `Platform.pc`, `Platform.ps3` (Xbox 360 is not yet supported)
`timeout`      | float   | Optional  | How long to wait for data before raising a timeout exception

----

#### \[Async\]Client.hello()

Send the initial "hello" packet to the FESL server.

---

#### \[Async\]Client.memcheck()

Send the response to the FESL server's "memcheck" challenge.

----

#### \[Async\]Client.login()

Send the login details to the FESL server.

----

#### \[Async\]Client.lookup_usernames(usernames, namespace)

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

from pybfbc2stats import Client, Platform, Namespace

client = Client('ea_account_name', 'ea_account_password', Platform.pc)
names = ['SickLittleMonkey', '[SuX] DeLuXe']
quoted = [quote(name) for name in names]
persona = client.lookup_usernames(quoted, Namespace.pc)
```

----

#### \[Async\]Client.lookup_username(username, namespace)

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

from pybfbc2stats import Client, Platform, Namespace

client = Client('ea_account_name', 'ea_account_password', Platform.ps3)
persona = client.lookup_username(quote('Major Brainhurt'), Namespace.pc)
```

----

#### \[Async\]Client.lookup_user_ids(user_ids, namespace)

Lookup a list of user ids and return any matching personas.

**Note**: Since this method accepts a `namespace` argument, it can lookup user ids in any namespace (on any platform), regardless of which `Platform` was used to create the client instance.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`user_ids`     | List[int]  | Required | 
`namespace`     | Namespace | Required | One of: `Namespace.pc`, `Namespace.ps3`, `Namespace.xbox360`

**Example**

```python
from pybfbc2stats import Client, Platform, Namespace

client = Client('ea_account_name', 'ea_account_password', Platform.pc)
persona = client.lookup_user_ids([232302860, 233866102], Namespace.xbox360)
```

----

#### \[Async\]Client.lookup_user_id(user_id, namespace)

Lookup a single user id and return any matching persona.

**Note**: Since this method accepts a `namespace` argument, it can lookup user ids in any namespace (on any platform), regardless of which `Platform` was used to create the client instance.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`user_id`     | int  | Required | 
`namespace`     | Namespace | Required | One of: `Namespace.pc`, `Namespace.ps3`, `Namespace.xbox360`

**Example**

```python
from pybfbc2stats import Client, Platform, Namespace

client = Client('ea_account_name', 'ea_account_password', Platform.pc)
persona = client.lookup_user_id(232302860, Namespace.xbox360)
```

----

#### \[Async\]Client.search_name(screen_name)

Find personas given a **url encoded/quoted** (partial) name on the client instance's platform. You can use `*` as a trailing wildcard.

**Note**: The FESL backend returns an error both if a) no matching results were found and b) too many matching results were found. So, be careful with wildcard characters in combination with short partial names.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`screen_name`     | str  | Required | **Url encoded/quoted** (partial) name

**Example**

```python
from urllib.parse import quote

from pybfbc2stats import Client, Platform

client = Client('ea_account_name', 'ea_account_password', Platform.pc)
results = client.search_name(quote('[=BL=] larryp11'))
```

----

#### \[Async\]Client.get_stats(userid, keys)

Retrieve a given list of stats attributes for a given player id on the client instance's platform.

**Arguments**

  Argument     | Type | Opt/Required | Note
---------------|------|--------------|-----
`userid`       | int  | Required | 
`keys`         | List[bytes] | Optional | By default, all available attributes are retrieved (see `STATS_KEYS` constant for details)

**Example**

```python
from pybfbc2stats import Client, Platform

client = Client('ea_account_name', 'ea_account_password', Platform.ps3)
stats = client.get_stats(223789857, [b'accuracy', b'kills', b'deaths', b'score', b'time'])
```

----

#### \[Async\]Client.get_leaderboard(min_rank, max_rank, sort_by, keys)

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
from pybfbc2stats import Client, Platform

client = Client('ea_account_name', 'ea_account_password', Platform.pc)
leaderboard = client.get_leaderboard(1, 50, b'time')
```
