import unittest

from pybfbc2stats import Error, ParameterError
from pybfbc2stats.payload import Payload


class PayloadTest(unittest.TestCase):
    def test_init(self):
        # GIVEN
        kwargs = {
            'bytes': b'bytes',
            'str': 'str',
            'int': 1,
            'float': 1.0,
            'none': None
        }

        # WHEN
        payload = Payload(**kwargs)

        # THEN
        self.assertEqual(b'bytes', payload.data.get('bytes'))
        self.assertEqual(b'str', payload.data.get('str'))
        self.assertEqual(b'1', payload.data.get('int'))
        self.assertEqual(b'1.0', payload.data.get('float'))
        self.assertEqual(b'', payload.data.get('none'))
        self.assertEqual(5, len(payload.data))

    def test_from_bytes(self):
        # GIVEN
        data = b'TXN=MemCheck\nresult='

        # WHEN
        payload = Payload.from_bytes(data)

        # THEN
        self.assertEqual(b'MemCheck', payload.data.get('TXN'))
        self.assertEqual(b'', payload.data.get('result'))
        self.assertEqual(2, len(payload.data))

    def test_bytes(self):
        # GIVEN
        payload = Payload(TXN=b'MemCheck', result=b'')

        # WHEN
        as_bytes = bytes(payload)

        # THEN
        self.assertEqual(b'TXN=MemCheck\nresult=', as_bytes)

    def test_len(self):
        # GIVEN
        payload = Payload(TXN=b'MemCheck', result=b'')

        # WHEN
        length = len(payload)

        # THEN
        self.assertEqual(20, length)

    def test_update(self):
        # GIVEN
        payload = Payload(unchanged='unchanged', change='original')

        # WHEN
        payload.update(change='updated', added='added')

        # THEN
        self.assertEqual(b'unchanged', payload.data.get('unchanged'))
        self.assertEqual(b'updated', payload.data.get('change'))
        self.assertEqual(b'added', payload.data.get('added'))
        self.assertEqual(3, len(payload.data))

    def test_set_scalar(self):
        # GIVEN
        payload = Payload(existing='existing')

        # WHEN
        payload.set('bytes', b'bytes')
        payload.set('str', 'str')
        payload.set('int', 1)
        payload.set('float', 1.0)
        payload.set('none', None)

        # THEN
        self.assertEqual(b'existing', payload.data.get('existing'))
        self.assertEqual(b'bytes', payload.data.get('bytes'))
        self.assertEqual(b'str', payload.data.get('str'))
        self.assertEqual(b'1', payload.data.get('int'))
        self.assertEqual(b'1.0', payload.data.get('float'))
        self.assertEqual(b'', payload.data.get('none'))
        self.assertEqual(6, len(payload.data))

    def test_set_overwrite_struct(self):
        # GIVEN
        payload = Payload(
            dict={
                'key': 'value',
                'other-key': 'other-value',
                'nested-dict': {
                    'sub-key': 'sub-value'
                }
            },
            list=['one', 'two', 'three']
        )

        # WHEN
        payload.set('dict', {'new-key': 'new-value'})
        payload.set('list', ['four'])

        # THEN
        self.assertEqual(b'new-value', payload.data.get('dict.new-key'))
        self.assertEqual(b'four', payload.data.get('list.0'))
        self.assertEqual(b'1', payload.data.get('list.[]'))
        self.assertEqual(3, len(payload.data))

    def test_set_dict(self):
        # GIVEN
        payload = Payload(existing='existing')

        # WHEN
        payload.set('scalar-dict', {
            'bytes': b'bytes',
            'str': 'str',
            'int': 1,
            'float': 1.0,
            'none': None
        })
        payload.set('nested-dict', {
            'key': {
                'bytes': b'bytes',
                'str': 'str',
                'int': 1,
                'float': 1.0,
                'none': None
            }
        })

        # THEN
        self.assertEqual(b'existing', payload.data.get('existing'))
        self.assertEqual(b'bytes', payload.data.get('scalar-dict.bytes'))
        self.assertEqual(b'str', payload.data.get('scalar-dict.str'))
        self.assertEqual(b'1', payload.data.get('scalar-dict.int'))
        self.assertEqual(b'1.0', payload.data.get('scalar-dict.float'))
        self.assertEqual(b'', payload.data.get('scalar-dict.none'))
        self.assertEqual(b'bytes', payload.data.get('nested-dict.key.bytes'))
        self.assertEqual(b'str', payload.data.get('nested-dict.key.str'))
        self.assertEqual(b'1', payload.data.get('nested-dict.key.int'))
        self.assertEqual(b'1.0', payload.data.get('nested-dict.key.float'))
        self.assertEqual(b'', payload.data.get('nested-dict.key.none'))
        self.assertEqual(11, len(payload.data))

    def test_set_list(self):
        # GIVEN
        payload = Payload(existing='existing')

        # WHEN
        payload.set('scalar-list', [b'bytes', 'str', 1, 1.0, None])
        payload.set('nested-list', [
            [b'bytes', 'str', 1, 1.0, None],
            [b'other-bytes', 'other-str', 2, 2.0, None]
        ])
        payload.set('dict-list', [
            {
                'bytes': b'bytes',
                'str': 'str',
                'int': 1,
                'float': 1.0,
                'none': None
            },
            {
                'bytes': b'other-bytes',
                'str': 'other-str',
                'int': 2,
                'float': 2.0,
                'none': None
            }
        ])

        # THEN
        self.assertEqual(b'existing', payload.data.get('existing'))
        self.assertEqual(b'bytes', payload.data.get('scalar-list.0'))
        self.assertEqual(b'str', payload.data.get('scalar-list.1'))
        self.assertEqual(b'1', payload.data.get('scalar-list.2'))
        self.assertEqual(b'1.0', payload.data.get('scalar-list.3'))
        self.assertEqual(b'', payload.data.get('scalar-list.4'))
        self.assertEqual(b'5', payload.data.get('scalar-list.[]'))
        self.assertEqual(b'bytes', payload.data.get('nested-list.0.0'))
        self.assertEqual(b'str', payload.data.get('nested-list.0.1'))
        self.assertEqual(b'1', payload.data.get('nested-list.0.2'))
        self.assertEqual(b'1.0', payload.data.get('nested-list.0.3'))
        self.assertEqual(b'', payload.data.get('nested-list.0.4'))
        self.assertEqual(b'5', payload.data.get('nested-list.0.[]'))
        self.assertEqual(b'other-bytes', payload.data.get('nested-list.1.0'))
        self.assertEqual(b'other-str', payload.data.get('nested-list.1.1'))
        self.assertEqual(b'2', payload.data.get('nested-list.1.2'))
        self.assertEqual(b'2.0', payload.data.get('nested-list.1.3'))
        self.assertEqual(b'', payload.data.get('nested-list.1.4'))
        self.assertEqual(b'5', payload.data.get('nested-list.1.[]'))
        self.assertEqual(b'2', payload.data.get('nested-list.[]'))
        self.assertEqual(b'bytes', payload.data.get('dict-list.0.bytes'))
        self.assertEqual(b'str', payload.data.get('dict-list.0.str'))
        self.assertEqual(b'1', payload.data.get('dict-list.0.int'))
        self.assertEqual(b'1.0', payload.data.get('dict-list.0.float'))
        self.assertEqual(b'', payload.data.get('dict-list.0.none'))
        self.assertEqual(b'other-bytes', payload.data.get('dict-list.1.bytes'))
        self.assertEqual(b'other-str', payload.data.get('dict-list.1.str'))
        self.assertEqual(b'2', payload.data.get('dict-list.1.int'))
        self.assertEqual(b'2.0', payload.data.get('dict-list.1.float'))
        self.assertEqual(b'', payload.data.get('dict-list.1.none'))
        self.assertEqual(b'2', payload.data.get('dict-list.[]'))
        self.assertEqual(31, len(payload.data))

    def test_get(self):
        # GIVEN
        payload = Payload(TXN=b'MemCheck', result=b'')

        # WHEN
        existing = payload.get('TXN')
        default = payload.get('missing', b'default')
        missing = payload.get('missing')

        # THEN
        self.assertEqual(b'MemCheck', existing)
        self.assertEqual(b'default', default)
        self.assertIsNone(missing)

    def test_get_str(self):
        # GIVEN
        payload = Payload(str='str')

        # WHEN
        existing = payload.get_str('str')
        default = payload.get_str('missing', 'default')
        missing = payload.get_str('missing')

        # THEN
        self.assertEqual('str', existing)
        self.assertEqual('default', default)
        self.assertIsNone(missing)

    def test_get_int(self):
        # GIVEN
        payload = Payload(int=1)

        # WHEN
        existing = payload.get_int('int')
        default = payload.get_int('missing', 0)
        missing = payload.get_int('missing')

        # THEN
        self.assertEqual(1, existing)
        self.assertEqual(0, default)
        self.assertIsNone(missing)

    def test_get_float(self):
        # GIVEN
        payload = Payload(float=1.0)

        # WHEN
        existing = payload.get_float('float')
        default = payload.get_float('missing', 0.0)
        missing = payload.get_float('missing')

        # THEN
        self.assertEqual(1.0, existing)
        self.assertEqual(0.0, default)
        self.assertIsNone(missing)

    def test_get_list(self):
        # GIVEN
        payload = Payload(list=[b'bytes', 'str', 1, 1.0, None])

        # WHEN
        existing = payload.get_list('list')
        default = payload.get_list('missing', [])
        missing = payload.get_list('missing')

        # THEN
        self.assertEqual([b'bytes', b'str', b'1', b'1.0', b''], existing)
        self.assertEqual([], default)
        self.assertIsNone(missing)

    def test_get_list_nested(self):
        # GIVEN
        payload = Payload(list=[
            [b'bytes', 'str', 1, 1.0, None],
            [b'other-bytes', 'other-str', 2, 2.0, None]
        ])

        # WHEN
        actual = payload.get_list('list')

        # THEN
        self.assertEqual([
            [b'bytes', b'str', b'1', b'1.0', b''],
            [b'other-bytes', b'other-str', b'2', b'2.0', b'']
        ], actual)

    def test_get_list_dict(self):
        # GIVEN
        payload = Payload(list=[
            {
                'bytes': b'bytes',
                'str': 'str',
                'int': 1,
                'float': 1.0,
                'none': None
            },
            {
                'bytes': b'other-bytes',
                'str': 'other-str',
                'int': 2,
                'float': 2.0,
                'none': None
            }
        ])

        # WHEN
        actual = payload.get_list('list')

        # THEN
        self.assertEqual([
            {
                'bytes': b'bytes',
                'str': b'str',
                'int': b'1',
                'float': b'1.0',
                'none': b''
            },
            {
                'bytes': b'other-bytes',
                'str': b'other-str',
                'int': b'2',
                'float': b'2.0',
                'none': b''
            }
        ], actual)

    def test_get_list_missing_length_indicator(self):
        # GIVEN
        payload = Payload.from_bytes(b'list.0=value')

        # WHEN/THEN
        self.assertRaises(Error, payload.get_list, 'list')

    def test_get_list_missing_index(self):
        # GIVEN
        payload = Payload.from_bytes(b'list.[]=1')

        # WHEN/THEN
        self.assertRaises(Error, payload.get_list, 'list')

    def test_get_list_not_a_struct(self):
        # GIVEN
        payload = Payload(key=b'value')

        # WHEN/THEN
        self.assertRaises(Error, payload.get_list, 'key')

    def test_get_list_not_a_list(self):
        # GIVEN
        payload = Payload(dict={
            'key': b'value'
        })

        # WHEN/THEN
        self.assertRaises(Error, payload.get_list, 'dict')

    def test_get_map(self):
        # GIVEN
        payload = Payload.from_bytes(
            b'map.{bytes}=bytes\nmap.{str}=str\n'
            b'map.{int}=1\nmap.{float}=1.0\nmap.none=\n'
            b'map.{}=5'
        )

        # WHEN
        existing = payload.get_map('map')
        default = payload.get_map('missing', {})
        missing = payload.get_map('missing')

        # THEN
        self.assertEqual({
            'bytes': b'bytes',
            'str': b'str',
            'int': b'1',
            'float': b'1.0',
            'none': b''
        }, existing)
        self.assertEqual({}, default)
        self.assertIsNone(missing)

    def test_get_map_nested(self):
        # GIVEN
        payload = Payload.from_bytes(
            b'map.{key}.{bytes}=bytes\nmap.{key}.{str}=str\n'
            b'map.{key}.{int}=1\nmap.{key}.{float}=1.0\nmap.{key}.none=\n'
            b'map.{key}.{}=5\n'
            b'map.{}=1'
        )

        # WHEN
        actual = payload.get_map('map')

        # THEN
        self.assertEqual({
            'key': {
                'bytes': b'bytes',
                'str': b'str',
                'int': b'1',
                'float': b'1.0',
                'none': b''
            }
        }, actual)

    def test_get_map_list(self):
        # GIVEN
        payload = Payload.from_bytes(
            b'map.{key}.0=bytes\nmap.{key}.1=str\n'
            b'map.{key}.2=1\nmap.{key}.3=1.0\nmap.{key}.4=\n'
            b'map.{key}.[]=5\n'
            b'map.{other-key}.0=other-bytes\nmap.{other-key}.1=other-str\n'
            b'map.{other-key}.2=2\nmap.{other-key}.3=2.0\nmap.{other-key}.4=\n'
            b'map.{other-key}.[]=5\n'
            b'map.{}=2'
        )

        # WHEN
        actual = payload.get_map('map')

        # THEN
        self.assertEqual({
            'key': [b'bytes', b'str', b'1', b'1.0', b''],
            'other-key': [b'other-bytes', b'other-str', b'2', b'2.0', b'']
        }, actual)

    def test_get_map_missing_length_indicator(self):
        # GIVEN
        payload = Payload.from_bytes(b'map.{key}=value')

        # WHEN/THEN
        self.assertRaises(Error, payload.get_map, 'map')

    def test_get_map_missing_key(self):
        # GIVEN
        payload = Payload.from_bytes(b'map.{}=1')

        # WHEN/THEN
        self.assertRaises(Error, payload.get_map, 'map')

    def test_get_map_not_a_struct(self):
        # GIVEN
        payload = Payload(key=b'value')

        # WHEN/THEN
        self.assertRaises(Error, payload.get_map, 'key')

    def test_get_list_not_a_map(self):
        # GIVEN
        payload = Payload(dict={
            'key': b'value'
        })

        # WHEN/THEN
        self.assertRaises(Error, payload.get_map, 'dict')

    def test_get_dict(self):
        # GIVEN
        payload = Payload(dict={
            'bytes': b'bytes',
            'str': 'str',
            'int': 1,
            'float': 1.0,
            'none': None
        })

        # WHEN
        existing = payload.get_dict('dict')
        default = payload.get_dict('missing', {})
        missing = payload.get_dict('missing')

        # THEN
        self.assertEqual({
            'bytes': b'bytes',
            'str': b'str',
            'int': b'1',
            'float': b'1.0',
            'none': b''
        }, existing)
        self.assertEqual({}, default)
        self.assertIsNone(missing)

    def test_get_dict_nested(self):
        # GIVEN
        payload = Payload(dict={
            'key': {
                'bytes': b'bytes',
                'str': 'str',
                'int': 1,
                'float': 1.0,
                'none': None
            }
        })

        # WHEN
        actual = payload.get_dict('dict')

        # THEN
        self.assertEqual({
            'key': {
                'bytes': b'bytes',
                'str': b'str',
                'int': b'1',
                'float': b'1.0',
                'none': b''
            }
        }, actual)

    def test_get_dict_list(self):
        # GIVEN
        payload = Payload(dict={
            'key': [b'bytes', 'str', 1, 1.0, None],
            'other-key': [b'other-bytes', 'other-str', 2, 2.0, None]
        })

        # WHEN
        actual = payload.get_dict('dict')

        # THEN
        self.assertEqual({
            'key': [b'bytes', b'str', b'1', b'1.0', b''],
            'other-key': [b'other-bytes', b'other-str', b'2', b'2.0', b'']
        }, actual)

    def test_get_dict_not_a_struct(self):
        # GIVEN
        payload = Payload(key=b'value')

        # WHEN/THEN
        self.assertRaises(Error, payload.get_dict, 'key')

    def test_personas_response(self):
        # GIVEN
        payload = Payload.from_bytes(b'personas.[]=1\npersonas.0=yeas-yuwn-ep-lon\nTXN=NuGetPersonas')

        # WHEN
        txn = payload.get_str('TXN')
        personas = payload.get_list('personas')

        # THEN
        self.assertEqual('NuGetPersonas', txn)
        self.assertEqual([b'yeas-yuwn-ep-lon'], personas)

    def test_user_lookup_response(self):
        # GIVEN
        payload = Payload.from_bytes(
            b'userInfo.0.namespace=PS3_SUB\nuserInfo.0.userId=891451503\nTXN=LookupUserInfo\n'
            b'userInfo.0.xuid=8030785869539906380\nuserInfo.0.userName=sam707\nuserInfo.[]=1'
        )

        # WHEN
        txn = payload.get_str('TXN')
        users = payload.get_list('userInfo')

        # THEN
        self.assertEqual('LookupUserInfo', txn)
        self.assertEqual([
            {'namespace': b'PS3_SUB', 'userId': b'891451503', 'xuid': b'8030785869539906380', 'userName': b'sam707'}
        ], users)

    def test_search_name_response(self):
        # GIVEN
        payload = Payload.from_bytes(
            b'users.[]=1\nusers.0.id=1038690899\nTXN=SearchOwners\nusers.0.name=Sam70786\n'
            b'nameSpaceId=XBL_SUB\nusers.0.type=1'
        )

        # WHEN
        txn = payload.get_str('TXN')
        namespace_id = payload.get_str('nameSpaceId')
        users = payload.get_list('users')

        # THEN
        self.assertEqual('SearchOwners', txn)
        self.assertEqual('XBL_SUB', namespace_id)
        self.assertEqual([
            {'id': b'1038690899', 'name': b'Sam70786', 'type': b'1'}
        ], users)

    def test_stats_response(self):
        # GIVEN
        payload = Payload.from_bytes(
            b'stats.1.key=losses\nstats.[]=3\nstats.2.value=16455.0\nTXN=GetStats\nstats.1.value=12006.0\n'
            b'stats.2.key=wins\nstats.0.value=28461.0\nstats.0.key=games'
        )

        # WHEN
        txn = payload.get_str('TXN')
        stats = payload.get_list('stats')

        # THEN
        self.assertEqual('GetStats', txn)
        self.assertEqual([
            {'key': b'games', 'value': b'28461.0'},
            {'key': b'losses', 'value': b'12006.0'},
            {'key': b'wins', 'value': b'16455.0'}
        ], stats)

    def test_dogtags_as_map_response(self):
        # GIVEN
        payload = Payload.from_bytes(
            b'values.{992138898}=UkVTUEFXTiBPTzcAAAAAAEWzfpIAARkA\nlastModified="2023-09-22 19%3a42%3a57.0"\n'
            b'state=1\nvalues.{1055242182}=QnJhaW4gV3JvdWdodAAAAEWw6+8AARkA\n'
            b'values.{1032604717}=bGVtZW5rb29sAAAAAAAAAEWw6+8AAQkA\n'
            b'values.{939363578}=RmF1eE5hbWVsZXNzAAAAAEWw68wAARkA\nTTL=0\nvalues.{}=10\n'
            b'values.{1055240877}=RmF3YXogZ2IAAAAAAAAAAEWw7AAAARcA\n'
            b'values.{1055254420}=RmVsdEltcGFsYTY2ODkyAEWw7AcAAQYA\n'
            b'values.{1055257806}=RGFya2xvcmQ5MHh4AAAAAEWw68QAAQAA\n'
            b'values.{1055257610}=TmlnaHRnYW1lcjI2NTcAAEWw6+AAAQMA\n'
            b'TXN=GetRecordAsMap\nvalues.{781949650}=TUlLODEzAAAAAAAAAAAAAEWw6+EAAQ4A\n'
            b'values.{1048348626}=UnlhbkRXeW5uZQAAAAAAAEWw7AkAAhkA'
        )

        # WHEN
        txn = payload.get_str('TXN')
        ttl = payload.get_int('TTL')
        state = payload.get_int('state')
        last_modified = payload.get_str('lastModified')
        values = payload.get_map('values')

        # THEN
        self.assertEqual('GetRecordAsMap', txn)
        self.assertEqual(0, ttl)
        self.assertEqual(1, state)
        self.assertEqual('2023-09-22 19:42:57.0', last_modified)
        self.assertEqual({
            '1055242182': b'QnJhaW4gV3JvdWdodAAAAEWw6+8AARkA',
            '1055257806': b'RGFya2xvcmQ5MHh4AAAAAEWw68QAAQAA',
            '939363578': b'RmF1eE5hbWVsZXNzAAAAAEWw68wAARkA',
            '1055257610': b'TmlnaHRnYW1lcjI2NTcAAEWw6+AAAQMA',
            '1048348626': b'UnlhbkRXeW5uZQAAAAAAAEWw7AkAAhkA',
            '1032604717': b'bGVtZW5rb29sAAAAAAAAAEWw6+8AAQkA',
            '1055254420': b'RmVsdEltcGFsYTY2ODkyAEWw7AcAAQYA',
            '992138898': b'UkVTUEFXTiBPTzcAAAAAAEWzfpIAARkA',
            '781949650': b'TUlLODEzAAAAAAAAAAAAAEWw6+EAAQ4A',
            '1055240877': b'RmF3YXogZ2IAAAAAAAAAAEWw7AAAARcA'
        }, values)

    def test_dogtags_as_list_response(self):
        # GIVEN
        payload = Payload.from_bytes(
            b'state=1\nvalues.5.value=bGVtZW5rb29sAAAAAAAAAEWw6+8AAQkA\nvalues.6.key=1055254420\nTTL=0\n'
            b'values.3.value=TmlnaHRnYW1lcjI2NTcAAEWw6+AAAQMA\nvalues.1.value=RGFya2xvcmQ5MHh4AAAAAEWw68QAAQAA\n'
            b'values.6.value=RmVsdEltcGFsYTY2ODkyAEWw7AcAAQYA\nvalues.9.key=1055240877\n'
            b'values.2.value=RmF1eE5hbWVsZXNzAAAAAEWw68wAARkA\nvalues.[]=10\n'
            b'values.8.value=TUlLODEzAAAAAAAAAAAAAEWw6+EAAQ4A\nvalues.4.key=1048348626\n'
            b'values.7.value=UkVTUEFXTiBPTzcAAAAAAEWzfpIAARkA\nvalues.9.value=RmF3YXogZ2IAAAAAAAAAAEWw7AAAARcA\n'
            b'values.7.key=992138898\nlastModified="2023-09-22 19%3a42%3a57.0"\nvalues.0.key=1055242182\n'
            b'values.5.key=1032604717\nvalues.1.key=1055257806\nvalues.3.key=1055257610\nvalues.2.key=939363578\n'
            b'values.8.key=781949650\nTXN=GetRecord\nvalues.0.value=QnJhaW4gV3JvdWdodAAAAEWw6+8AARkA\n'
            b'values.4.value=UnlhbkRXeW5uZQAAAAAAAEWw7AkAAhkA'
        )

        # WHEN
        txn = payload.get_str('TXN')
        ttl = payload.get_int('TTL')
        state = payload.get_int('state')
        last_modified = payload.get_str('lastModified')
        values = payload.get_list('values')

        # THEN
        self.assertEqual('GetRecord', txn)
        self.assertEqual(0, ttl)
        self.assertEqual(1, state)
        self.assertEqual('2023-09-22 19:42:57.0', last_modified)
        self.assertEqual([
            {'key': b'1055242182', 'value': b'QnJhaW4gV3JvdWdodAAAAEWw6+8AARkA'},
            {'key': b'1055257806', 'value': b'RGFya2xvcmQ5MHh4AAAAAEWw68QAAQAA'},
            {'key': b'939363578', 'value': b'RmF1eE5hbWVsZXNzAAAAAEWw68wAARkA'},
            {'key': b'1055257610', 'value': b'TmlnaHRnYW1lcjI2NTcAAEWw6+AAAQMA'},
            {'key': b'1048348626', 'value': b'UnlhbkRXeW5uZQAAAAAAAEWw7AkAAhkA'},
            {'key': b'1032604717', 'value': b'bGVtZW5rb29sAAAAAAAAAEWw6+8AAQkA'},
            {'key': b'1055254420', 'value': b'RmVsdEltcGFsYTY2ODkyAEWw7AcAAQYA'},
            {'key': b'992138898', 'value': b'UkVTUEFXTiBPTzcAAAAAAEWzfpIAARkA'},
            {'key': b'781949650', 'value': b'TUlLODEzAAAAAAAAAAAAAEWw6+EAAQ4A'},
            {'key': b'1055240877', 'value': b'RmF3YXogZ2IAAAAAAAAAAEWw7AAAARcA'}
        ], values)

    def test_leaderboard_response(self):
        # GIVEN
        payload = Payload.from_bytes(
            b'stats.4.addStats.2.value=1.1630278E7\nstats.2.owner=959040406\nstats.4.addStats.1.key=kills\n'
            b'stats.0.addStats.1.key=kills\nstats.4.addStats.0.value=151531.0\nstats.2.addStats.2.key=score\n'
            b'stats.0.value=2.4056603E7\nstats.0.addStats.[]=4\nstats.1.addStats.0.value=292627.0\n'
            b'stats.0.addStats.0.value=988609.0\nstats.2.rank=3\nstats.0.addStats.3.value=6.6336188019E7\n'
            b'stats.1.rank=2\nstats.4.name="K5Q Blan"\nstats.2.addStats.1.key=kills\nstats.3.addStats.1.key=kills\n'
            b'stats.2.name="o lNiiNJA"\nstats.3.owner=925212106\nstats.4.rank=5\nstats.4.addStats.[]=4\n'
            b'stats.2.addStats.3.key=time\nstats.3.addStats.3.key=time\nstats.0.rank=1\nstats.0.addStats.2.key=score\n'
            b'stats.3.addStats.2.key=score\nstats.2.addStats.0.value=127087.0\nstats.4.addStats.3.key=time\n'
            b'TXN=GetTopNAndStats\nstats.1.addStats.[]=4\nstats.3.addStats.3.value=2.5479985997E7\n'
            b'stats.4.value=1.1630278E7\nstats.2.addStats.0.key=deaths\nstats.3.addStats.2.value=1.2270119E7\n'
            b'stats.3.value=1.2270119E7\nstats.4.addStats.3.value=2.2121341986E7\nstats.1.addStats.3.key=time\n'
            b'stats.3.addStats.0.value=180779.0\nstats.1.owner=853198764\nstats.[]=5\nstats.1.value=1.553427E7\n'
            b'stats.1.addStats.1.key=kills\nstats.2.addStats.1.value=636392.0\n'
            b'stats.1.addStats.3.value=4.3991928017E7\nstats.0.owner=905760050\nstats.0.addStats.2.value=2.4056603E7\n'
            b'stats.0.addStats.3.key=time\nstats.0.addStats.0.key=deaths\nstats.2.addStats.2.value=1.3002937E7\n'
            b'stats.4.addStats.1.value=568653.0\nstats.2.value=1.3002937E7\nstats.1.addStats.0.key=deaths\n'
            b'stats.3.addStats.0.key=deaths\nstats.3.name=Schmittepitter\nstats.0.addStats.1.value=1082418.0\n'
            b'stats.2.addStats.[]=4\nstats.3.addStats.1.value=572390.0\nstats.1.name="BONE 815"\n'
            b'stats.4.addStats.0.key=deaths\nstats.3.rank=4\nstats.1.addStats.2.key=score\nstats.0.name=daddyo21252\n'
            b'stats.4.addStats.2.key=score\nstats.3.addStats.[]=4\nstats.1.addStats.1.value=738204.0\n'
            b'stats.2.addStats.3.value=2.1566129983E7\nstats.4.owner=987817822\nstats.1.addStats.2.value=1.553427E7'
        )

        # WHEN
        txn = payload.get('TXN')
        stats = payload.get_list('stats')

        # THEN
        self.assertEqual(b'GetTopNAndStats', txn)
        self.assertEqual([
            {
                'owner': b'905760050',
                'name': b'daddyo21252',
                'rank': b'1',
                'value': b'2.4056603E7',
                'addStats': [
                    {'key': b'deaths', 'value': b'988609.0'},
                    {'key': b'kills', 'value': b'1082418.0'},
                    {'key': b'score', 'value': b'2.4056603E7'},
                    {'key': b'time', 'value': b'6.6336188019E7'},
                ]
            },
            {
                'owner': b'853198764',
                'name': b'"BONE 815"',
                'rank': b'2',
                'value': b'1.553427E7',
                'addStats': [
                    {'key': b'deaths', 'value': b'292627.0'},
                    {'key': b'kills', 'value': b'738204.0'},
                    {'key': b'score', 'value': b'1.553427E7'},
                    {'key': b'time', 'value': b'4.3991928017E7'},
                ]
            },
            {
                'owner': b'959040406',
                'name': b'"o lNiiNJA"',
                'rank': b'3',
                'value': b'1.3002937E7',
                'addStats': [
                    {'key': b'deaths', 'value': b'127087.0'},
                    {'key': b'kills', 'value': b'636392.0'},
                    {'key': b'score', 'value': b'1.3002937E7'},
                    {'key': b'time', 'value': b'2.1566129983E7'},
                ]
            },
            {
                'owner': b'925212106',
                'name': b'Schmittepitter',
                'rank': b'4',
                'value': b'1.2270119E7',
                'addStats': [
                    {'key': b'deaths', 'value': b'180779.0'},
                    {'key': b'kills', 'value': b'572390.0'},
                    {'key': b'score', 'value': b'1.2270119E7'},
                    {'key': b'time', 'value': b'2.5479985997E7'},
                ]
            },
            {
                'owner': b'987817822',
                'name': b'"K5Q Blan"',
                'rank': b'5',
                'value': b'1.1630278E7',
                'addStats': [
                    {'key': b'deaths', 'value': b'151531.0'},
                    {'key': b'kills', 'value': b'568653.0'},
                    {'key': b'score', 'value': b'1.1630278E7'},
                    {'key': b'time', 'value': b'2.2121341986E7'},
                ]
            }
        ], stats)

    def test_conn_response(self):
        # GIVEN
        payload = Payload.from_bytes(b'TIME=1700680166\nTID=1\nactivityTimeoutSecs=240\nPROT=2')

        # WHEN
        time = payload.get_int('TIME')
        tid = payload.get_int('TID')
        ats = payload.get_int('activityTimeoutSecs')
        prot = payload.get_int('PROT')

        # THEN
        self.assertEqual(1700680166, time)
        self.assertEqual(1, tid)
        self.assertEqual(240, ats)
        self.assertEqual(2, prot)

    def test_gdat_response(self):
        # GIVEN
        payload = Payload.from_bytes(
            b'JP=2\nB-U-location=nrt\nHN=beach.server.p\nB-U-level=levels/wake_island_s\nN=nrtps3313604\n'
            b'I=109.200.221.166\nJ=O\nHU=201104017\nB-U-Time="T%3a20.02 S%3a 9.81 L%3a 0.00"\nV=1.0\n'
            b'B-U-gamemode=CONQUEST\nP=26016\nB-U-trial=RETAIL\nB-U-balance=NORMAL\n'
            b'B-U-hash=8FF089DA-0DE7-0470-EF0F-0D4C905B7DC5\nB-numObservers=0\nTYPE=G\nLID=257\n'
            b'B-U-Frames="T%3a 300 B%3a 1"\nB-version=RETAIL421378\nQP=0\nMP=24\nB-U-type=RANKED\nB-U-playgroup=YES\n'
            b'B-U-public=NO\nGID=838009\nPL=PC\nB-U-elo=1000\nB-maxObservers=0\nPW=0\nTID=19\nB-U-coralsea=NO\nAP=0'
        )

        # WHEN/THEN
        self.assertEqual(2, payload.get_int('JP'))
        self.assertEqual('nrt', payload.get_str('B-U-location'))
        self.assertEqual('beach.server.p', payload.get_str('HN'))
        self.assertEqual('levels/wake_island_s', payload.get_str('B-U-level'))
        self.assertEqual('nrtps3313604', payload.get_str('N'))
        self.assertEqual('109.200.221.166', payload.get_str('I'))
        self.assertEqual('O', payload.get_str('J'))
        self.assertEqual(201104017, payload.get_int('HU'))
        self.assertEqual('T:20.02 S: 9.81 L: 0.00', payload.get_str('B-U-Time'))
        self.assertEqual('1.0', payload.get_str('V'))
        self.assertEqual('CONQUEST', payload.get_str('B-U-gamemode'))
        self.assertEqual(26016, payload.get_int('P'))
        self.assertEqual('RETAIL', payload.get_str('B-U-trial'))
        self.assertEqual('NORMAL', payload.get_str('B-U-balance'))
        self.assertEqual('8FF089DA-0DE7-0470-EF0F-0D4C905B7DC5', payload.get_str('B-U-hash'))
        self.assertEqual(0, payload.get_int('B-numObservers'))
        self.assertEqual('G', payload.get_str('TYPE'))
        self.assertEqual(257, payload.get_int('LID'))
        self.assertEqual('T: 300 B: 1', payload.get_str('B-U-Frames'))
        self.assertEqual('RETAIL421378', payload.get_str('B-version'))
        self.assertEqual(0, payload.get_int('QP'))
        self.assertEqual(24, payload.get_int('MP'))
        self.assertEqual('RANKED', payload.get_str('B-U-type'))
        self.assertEqual('YES', payload.get_str('B-U-playgroup'))
        self.assertEqual('NO', payload.get_str('B-U-public'))
        self.assertEqual(838009, payload.get_int('GID'))
        self.assertEqual('PC', payload.get_str('PL'))
        self.assertEqual(1000, payload.get_int('B-U-elo'))
        self.assertEqual(0, payload.get_int('B-maxObservers'))
        self.assertEqual(0, payload.get_int('PW'))
        self.assertEqual(19, payload.get_int('TID'))
        self.assertEqual('NO', payload.get_str('B-U-coralsea'))
        self.assertEqual(0, payload.get_int('AP'))
