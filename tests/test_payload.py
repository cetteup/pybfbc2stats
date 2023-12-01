import unittest
from typing import List

from pybfbc2stats import Error
from pybfbc2stats.constants import MagicParseKey
from pybfbc2stats.payload import Payload


def join_data(lines: List[bytes]) -> bytes:
    return b'\n'.join(lines)


class PayloadTest(unittest.TestCase):
    def test_init(self):
        # GIVEN
        kwargs = {
            'bytes': b'bytes',
            'str': 'str',
            'int': 1,
            'float': 1.0,
            'bool': True,
            'none': None
        }

        # WHEN
        payload = Payload(**kwargs)

        # THEN
        self.assertEqual(b'bytes', payload.data.get('bytes'))
        self.assertEqual('str', payload.data.get('str'))
        self.assertEqual(1, payload.data.get('int'))
        self.assertEqual(1.0, payload.data.get('float'))
        self.assertEqual(True, payload.data.get('float'))
        self.assertEqual(None, payload.data.get('none'))
        self.assertEqual(6, len(payload.data))

    def test_from_bytes(self):
        # GIVEN
        data = b'TXN=MemCheck\nresult='

        # WHEN
        actual = Payload.from_bytes(data)

        # THEN
        expected = Payload(TXN=b'MemCheck', result=b'')
        self.assertEqual(expected, actual)

    def test_from_bytes_parsed(self):
        # GIVEN
        data = join_data([
            b'bytes="some%20bytes"', b'str="a%20str"', b'int=1', b'float=1.0', b'bool=1', b'unsupported=bytes', b'none='
        ])
        parse_map = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'unsupported': tuple
        }

        # WHEN
        actual = Payload.from_bytes(data, parse_map)

        # THEN
        expected = Payload(
            bytes=b'"some%20bytes"',
            str='a str',
            int=1,
            float=1.0,
            bool=True,
            unsupported=b'bytes',
            none=b''
        )
        self.assertEqual(expected, actual)

    def test_from_bytes_parsed_with_fallback(self):
        # GIVEN
        data = join_data([
            b'bytes="some%20bytes"', b'str="a%20str"', b'int=1', b'float=1.0', b'bool=1', b'none='
        ])
        parse_map = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            MagicParseKey.fallback: str
        }

        # WHEN
        actual = Payload.from_bytes(data, parse_map)

        # THEN
        expected = Payload(bytes='some bytes', str='a str', int=1, float=1.0, bool=True, none='')
        self.assertEqual(expected, actual)

    def test_from_bytes_list(self):
        # GIVEN
        data = join_data([b'list.0=bytes', b'list.1=str', b'list.2=1', b'list.3=1.0', b'list.4=', b'list.[]=5'])

        # WHEN
        actual = Payload.from_bytes(data)

        # THEN
        expected = Payload(list=[b'bytes', b'str', b'1', b'1.0', b''])
        self.assertEqual(expected, actual)

    def test_from_bytes_list_nested(self):
        # GIVEN
        data = join_data([
            b'list.0.0=bytes', b'list.0.1=str', b'list.0.2=1', b'list.0.3=1.0', b'list.0.4=',
            b'list.0.[]=5',
            b'list.1.0=other-bytes', b'list.1.1=other-str', b'list.1.2=2', b'list.1.3=2.0', b'list.1.4=',
            b'list.1.[]=5',
            b'list.[]=2'
        ])

        # WHEN
        actual = Payload.from_bytes(data)

        # THEN
        expected = Payload(list=[
            [b'bytes', b'str', b'1', b'1.0', b''],
            [b'other-bytes', b'other-str', b'2', b'2.0', b'']
        ])
        self.assertEqual(expected, actual)

    def test_from_bytes_list_dict(self):
        # GIVEN
        data = join_data([
            b'list.0.bytes=bytes', b'list.0.str=str', b'list.0.int=1', b'list.0.float=1.0', b'list.0.none=',
            b'list.1.bytes=other-bytes', b'list.1.str=other-str', b'list.1.int=2', b'list.1.float=2.0', b'list.1.none=',
            b'list.[]=2'
        ])

        # WHEN
        actual = Payload.from_bytes(data)

        # THEN
        expected = Payload(list=[
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
        ])
        self.assertEqual(expected, actual)

    def test_from_bytes_list_parsed_str(self):
        # GIVEN
        data = join_data([
            b'str.0="quoted value"', b'str.1=encoded%20value', b'str.2="quoted%20and%20encoded%20value"', b'str.[]=3',
        ])
        parse_map = {
            MagicParseKey.index: str
        }

        # WHEN
        payload = Payload.from_bytes(data, parse_map)

        # THEN
        self.assertEqual(['quoted value', 'encoded value', 'quoted and encoded value'], payload.data.get('str'))

    def test_from_bytes_list_parsed_int(self):
        # GIVEN
        data = join_data([
            b'int.0=1', b'int.1=-1', b'int.[]=2',
        ])
        parse_map = {
            MagicParseKey.index: int
        }

        # WHEN
        payload = Payload.from_bytes(data, parse_map)

        # THEN
        self.assertEqual([1, -1], payload.data.get('int'))

    def test_from_bytes_list_parsed_float(self):
        # GIVEN
        data = join_data([
            b'float.0=1.0', b'float.1=-1.0', b'float.2=3.22E7', b'float.3=3.22E-7', b'float.[]=4',
        ])
        parse_map = {
            MagicParseKey.index: float
        }

        # WHEN
        payload = Payload.from_bytes(data, parse_map)

        # THEN
        self.assertEqual([1.0, -1.0, 3.22E7, 3.22E-7], payload.data.get('float'))

    def test_from_bytes_list_parsed_bool(self):
        # GIVEN
        data = join_data([
            b'bool.0=1', b'bool.1=0', b'bool.2=YES', b'bool.3=NO', b'bool.[]=4',
        ])
        parse_map = {
            MagicParseKey.index: bool
        }

        # WHEN
        payload = Payload.from_bytes(data, parse_map)

        # THEN
        self.assertEqual([True, False, True, False], payload.data.get('bool'))

    def test_from_bytes_list_parsed_nested(self):
        # GIVEN
        data = join_data([
            b'nested.0.0=1', b'nested.0.1=2', b'nested.0.2=3', b'nested.0.3=4', b'nested.0.4=5',
            b'nested.0.[]=5', b'nested.[]=1',
        ])
        parse_map = {
            MagicParseKey.index: int
        }

        # WHEN
        payload = Payload.from_bytes(data, parse_map)

        # THEN
        self.assertEqual([[1, 2, 3, 4, 5]], payload.data.get('nested'))

    def test_from_bytes_list_parsed_dict(self):
        # GIVEN
        data = join_data([
            b'dict.0.bytes=bytes', b'dict.0.str=str', b'dict.0.int=1', b'dict.0.float=1.0', b'dict.0.none=',
            b'dict.[]=1'
        ])
        parse_map = {
            'str': str,
            'int': int,
            'float': float
        }

        # WHEN
        payload = Payload.from_bytes(data, parse_map)

        # THEN
        self.assertEqual([{
            'bytes': b'bytes',
            'str': 'str',
            'int': 1,
            'float': 1.0,
            'none': b''
        }], payload.data.get('dict'))

    def test_from_bytes_list_missing_index(self):
        # GIVEN
        data = b'list.[]=1'

        # WHEN/THEN
        self.assertRaises(Error, Payload.from_bytes, data)

    def test_from_bytes_dict(self):
        # GIVEN
        data = join_data([
            b'dict.bytes=bytes', b'dict.str=str', b'dict.int=1', b'dict.float=1.0', b'dict.none=',
        ])

        actual = Payload.from_bytes(data)

        # THEN
        expected = Payload(dict={
            'bytes': b'bytes',
            'str': b'str',
            'int': b'1',
            'float': b'1.0',
            'none': b''
        })
        self.assertEqual(expected, actual)

    def test_from_bytes_dict_nested(self):
        # GIVEN
        data = join_data([
            b'dict.key.bytes=bytes', b'dict.key.str=str',
            b'dict.key.int=1', b'dict.key.float=1.0', b'dict.key.none=',
        ])

        # WHEN
        actual = Payload.from_bytes(data)

        # THEN
        expected = Payload(dict={
            'key': {
                'bytes': b'bytes',
                'str': b'str',
                'int': b'1',
                'float': b'1.0',
                'none': b''
            }
        })
        self.assertEqual(expected, actual)

    def test_from_bytes_dict_list(self):
        # GIVEN
        data = join_data([
            b'dict.key.0=bytes', b'dict.key.1=str', b'dict.key.2=1', b'dict.key.3=1.0', b'dict.key.4=',
            b'dict.key.[]=5',
            b'dict.other-key.0=other-bytes', b'dict.other-key.1=other-str', b'dict.other-key.2=2', b'dict.other-key.3=2.0', b'dict.other-key.4=',
            b'dict.other-key.[]=5',
        ])

        # WHEN
        actual = Payload.from_bytes(data)

        # THEN
        expected = Payload(dict={
            'key': [b'bytes', b'str', b'1', b'1.0', b''],
            'other-key': [b'other-bytes', b'other-str', b'2', b'2.0', b'']
        })
        self.assertEqual(expected, actual)

    def test_from_bytes_dict_parsed(self):
        # GIVEN
        data = join_data([
            b'dict.bytes=bytes', b'dict.str="a%20str"', b'dict.int=1', b'dict.float=1.0', b'dict.none=',
        ])
        parse_map = {
            'str': str,
            'int': int,
            'float': float
        }

        # WHEN
        actual = Payload.from_bytes(data, parse_map)

        # THEN
        expected = Payload(dict={
            'bytes': b'bytes',
            'str': 'a str',
            'int': 1,
            'float': 1.0,
            'none': b''
        })
        self.assertEqual(expected, actual)

    def test_from_bytes_map_missing_key(self):
        # GIVEN
        data = b'map.{}=1'

        # WHEN/THEN
        self.assertRaises(Error, Payload.from_bytes, data)

    def test_from_bytes_parse_error(self):
        # GIVEN
        non_utf8_str_data = b'str=\xac\x1d5\x08'
        non_int_data = b'int=value'
        non_float_data = b'float=value'
        non_bool_data = b'bool=value'

        # WHEN/THEN
        self.assertRaises(Error, Payload.from_bytes, non_utf8_str_data, {'str': str})
        self.assertRaises(Error, Payload.from_bytes, non_int_data, {'int': int})
        self.assertRaises(Error, Payload.from_bytes, non_float_data, {'float': float})
        self.assertRaises(Error, Payload.from_bytes, non_bool_data, {'bool': bool})

    def test_bytes(self):
        # GIVEN
        payload = Payload(TXN='MemCheck', result=None)

        # WHEN
        actual = bytes(payload)

        # THEN
        expected = join_data([b'TXN=MemCheck', b'result='])
        self.assertEqual(expected, actual)

    def test_bytes_list(self):
        # GIVEN
        payload = Payload(list=[b'bytes', 'str', 1, 1.0, True, None])

        # WHEN
        actual = bytes(payload)

        # THEN
        expected = join_data([
            b'list.0=bytes', b'list.1=str', b'list.2=1', b'list.3=1.0', b'list.4=1', b'list.5=',
            b'list.[]=6'
        ])
        self.assertEqual(expected, actual)

    def test_bytes_list_nested(self):
        # GIVEN
        payload = Payload(list=[
            [b'bytes', 'str', 1, 1.0, True, None],
            [b'other-bytes', 'other-str', 2, 2.0, False, None]
        ])

        # WHEN
        actual = bytes(payload)

        # THEN
        expected = join_data([
            b'list.0.0=bytes', b'list.0.1=str',
            b'list.0.2=1', b'list.0.3=1.0', b'list.0.4=1',b'list.0.5=',
            b'list.0.[]=6',
            b'list.1.0=other-bytes', b'list.1.1=other-str',
            b'list.1.2=2', b'list.1.3=2.0', b'list.1.4=0', b'list.1.5=',
            b'list.1.[]=6',
            b'list.[]=2'
        ])
        self.assertEqual(expected, actual)

    def test_bytes_list_dict(self):
        # GIVEN
        payload = Payload(list=[
            {
                'bytes': b'bytes',
                'str': 'str',
                'int': 1,
                'float': 1.0,
                'bool': True,
                'none': None
            },
            {
                'bytes': b'other-bytes',
                'str': 'other-str',
                'int': 2,
                'float': 2.0,
                'bool': False,
                'none': None
            }
        ])

        # WHEN
        actual = bytes(payload)

        # THEN
        expected = join_data([
            b'list.0.bytes=bytes', b'list.0.str=str',
            b'list.0.int=1', b'list.0.float=1.0', b'list.0.bool=1', b'list.0.none=',
            b'list.1.bytes=other-bytes', b'list.1.str=other-str',
            b'list.1.int=2', b'list.1.float=2.0', b'list.1.bool=0', b'list.1.none=',
            b'list.[]=2'
        ])
        self.assertEqual(expected, actual)

    def test_bytes_dict(self):
        # GIVEN
        payload = Payload(dict={
            'bytes': b'bytes',
            'str': 'str',
            'int': 1,
            'float': 1.0,
            'bool': True,
            'none': None
        })

        # WHEN
        actual = bytes(payload)

        # THEN
        expected = join_data([
            b'dict.bytes=bytes', b'dict.str=str', b'dict.int=1', b'dict.float=1.0', b'dict.bool=1', b'dict.none=',
        ])
        self.assertEqual(expected, actual)

    def test_bytes_dict_nested(self):
        # GIVEN
        payload = Payload(dict={
            'key': {
                'bytes': b'bytes',
                'str': 'str',
                'int': 1,
                'float': 1.0,
                'bool': True,
                'none': None
            }
        })

        # WHEN
        actual = bytes(payload)

        # THEN
        expected = join_data([
            b'dict.key.bytes=bytes', b'dict.key.str=str',
            b'dict.key.int=1', b'dict.key.float=1.0', b'dict.key.bool=1', b'dict.key.none='
        ])
        self.assertEqual(expected, actual)

    def test_bytes_dict_list(self):
        # GIVEN
        payload =Payload(dict={
            'key': [b'bytes', 'str', 1, 1.0, True, None],
            'other-key': [b'other-bytes', 'other-str', 2, 2.0, False, None]
        })

        # WHEN
        actual = bytes(payload)

        # THEN
        expected = join_data([
            b'dict.key.0=bytes', b'dict.key.1=str',
            b'dict.key.2=1', b'dict.key.3=1.0', b'dict.key.4=1', b'dict.key.5=',
            b'dict.key.[]=6',
            b'dict.other-key.0=other-bytes', b'dict.other-key.1=other-str',
            b'dict.other-key.2=2', b'dict.other-key.3=2.0', b'dict.other-key.4=0', b'dict.other-key.5=',
            b'dict.other-key.[]=6',
        ])
        self.assertEqual(expected, actual)

    def test_len(self):
        # GIVEN
        payload = Payload(TXN=b'MemCheck', result=b'')

        # WHEN
        length = len(payload)

        # THEN
        self.assertEqual(20, length)

    def test_eq(self):
        # GIVEN
        one = Payload(TXN=b'MemCheck', result=b'')
        two = Payload(TXN=b'MemCheck', result=b'')
        three = Payload(TXN=b'Ping')
        other = dict()

        # WHEN/THEN
        self.assertTrue(one == one)
        self.assertTrue(one == two)
        self.assertFalse(one == three)
        self.assertFalse(one == other)
        self.assertTrue(two == two)
        self.assertFalse(two == three)
        self.assertFalse(two == other)
        self.assertTrue(three == three)
        self.assertFalse(three == other)

    def test_getitem(self):
        # GIVEN
        payload = Payload(
            bytes=b'bytes',
            str='str',
            int=1,
            float=1.0,
            none=None
        )

        # WHEN/THEN
        self.assertEqual(b'bytes', payload['bytes'])
        self.assertEqual('str', payload['str'])
        self.assertEqual(1, payload['int'])
        self.assertEqual(1.0, payload['float'])
        self.assertEqual(None, payload['none'])
        self.assertRaises(KeyError, payload.__getitem__, 'missing')

    def test_setitem(self):
        # GIVEN
        payload = Payload(change='original')

        # WHEN
        payload['change'] = 'updated'
        payload['bytes'] = b'bytes'
        payload['str'] = 'str'
        payload['int'] = 1
        payload['float'] = 1.0
        payload['none'] = None

        # THEN
        self.assertEqual('updated', payload.data.get('change'))
        self.assertEqual(b'bytes', payload.data.get('bytes'))
        self.assertEqual('str', payload.data.get('str'))
        self.assertEqual(1, payload.data.get('int'))
        self.assertEqual(1.0, payload.data.get('float'))
        self.assertEqual(None, payload.data.get('none'))

    def test_update(self):
        # GIVEN
        payload = Payload(unchanged='unchanged', change='original')

        # WHEN
        payload.update(change='updated', added='added')

        # THEN
        self.assertEqual('unchanged', payload.data.get('unchanged'))
        self.assertEqual('updated', payload.data.get('change'))
        self.assertEqual('added', payload.data.get('added'))
        self.assertEqual(3, len(payload.data))

    def test_pop(self):
        # GIVEN
        payload = Payload(existing='existing')

        # WHEN
        popped = payload.pop('existing')

        # THEN
        self.assertFalse('existing' in payload.data)
        self.assertEqual('existing', popped)

    def test_cast_to_dict(self):
        # GIVEN
        payload = Payload(
            bytes=b'bytes',
            str='str',
            int=1,
            float=1.0,
            none=None
        )

        # WHEN
        actual = dict(payload)

        # THEN
        self.assertEqual({
            'bytes': b'bytes',
            'str': 'str',
            'int': 1,
            'float': 1.0,
            'none': None
        }, actual)

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
        payload['dict'] = {'new-key': 'new-value'}
        payload['list'] = ['four']

        # THEN
        self.assertEqual({'new-key': 'new-value'}, payload.data.get('dict'))
        self.assertEqual(['four'], payload.data.get('list'))
        self.assertEqual(2, len(payload.data))

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
        payload = Payload(
            str='str',
            str_quoted='"a%20str"',
            encoded=b'str',
            encoded_quoted=b'"a%20str"',
        )

        # WHEN
        existing = payload.get_str('str')
        existing_quoted = payload.get_str('str_quoted')
        encoded = payload.get_str('encoded')
        encoded_quoted = payload.get_str('encoded_quoted')
        default = payload.get_str('missing', 'default')
        missing = payload.get_str('missing')

        # THEN
        self.assertEqual('str', existing)
        self.assertEqual('a str', existing_quoted)
        self.assertEqual('str', encoded)
        self.assertEqual('a str', encoded_quoted)
        self.assertEqual('default', default)
        self.assertIsNone(missing)

    def test_get_int(self):
        # GIVEN
        payload = Payload(int=1, encoded=b'1')

        # WHEN
        existing = payload.get_int('int')
        encoded = payload.get_int('encoded')
        default = payload.get_int('missing', 0)
        missing = payload.get_int('missing')

        # THEN
        self.assertEqual(1, existing)
        self.assertEqual(1, encoded)
        self.assertEqual(0, default)
        self.assertIsNone(missing)

    def test_get_float(self):
        # GIVEN
        payload = Payload(float=1.0, encoded=b'1.0')

        # WHEN
        existing = payload.get_float('float')
        encoded = payload.get_float('encoded')
        default = payload.get_float('missing', 0.0)
        missing = payload.get_float('missing')

        # THEN
        self.assertEqual(1.0, existing)
        self.assertEqual(1.0, encoded)
        self.assertEqual(0.0, default)
        self.assertIsNone(missing)

    def test_get_bool(self):
        # GIVEN
        payload = Payload(true=1, false=0, encoded=b'YES')

        # WHEN
        true = payload.get_bool('true')
        false = payload.get_bool('false')
        encoded = payload.get_bool('encoded')
        default = payload.get_bool('missing', True)
        missing = payload.get_bool('missing')

        # THEN
        self.assertTrue(true)
        self.assertFalse(false)
        self.assertTrue(encoded)
        self.assertTrue(default)
        self.assertIsNone(missing)

    def test_get_list(self):
        # GIVEN
        payload = Payload(list=[b'bytes', 'str', 1, 1.0, None])

        # WHEN
        existing = payload.get_list('list')
        default = payload.get_list('missing', [])
        missing = payload.get_list('missing')

        # THEN
        self.assertEqual([b'bytes', 'str', 1, 1.0, None], existing)
        self.assertEqual([], default)
        self.assertIsNone(missing)

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
        data = join_data([
            b'map.{bytes}=bytes', b'map.{str}=str',
            b'map.{int}=1', b'map.{float}=1.0', b'map.none=',
            b'map.{}=5'
        ])
        payload = Payload.from_bytes(data)

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
        data = join_data([
            b'map.{key}.{bytes}=bytes', b'map.{key}.{str}=str',
            b'map.{key}.{int}=1', b'map.{key}.{float}=1.0', b'map.{key}.none=',
            b'map.{key}.{}=5',
            b'map.{}=1'
        ])
        payload = Payload.from_bytes(data)

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
        data = join_data([
            b'map.{key}.0=bytes', b'map.{key}.1=str',
            b'map.{key}.2=1', b'map.{key}.3=1.0', b'map.{key}.4=',
            b'map.{key}.[]=5',
            b'map.{other-key}.0=other-bytes', b'map.{other-key}.1=other-str',
            b'map.{other-key}.2=2', b'map.{other-key}.3=2.0', b'map.{other-key}.4=',
            b'map.{other-key}.[]=5',
            b'map.{}=2'
        ])
        payload = Payload.from_bytes(data)

        # WHEN
        actual = payload.get_map('map')

        # THEN
        self.assertEqual({
            'key': [b'bytes', b'str', b'1', b'1.0', b''],
            'other-key': [b'other-bytes', b'other-str', b'2', b'2.0', b'']
        }, actual)

    def test_get_map_parsed(self):
        # GIVEN
        data = join_data([
            b'map.{bytes}=bytes', b'map.{str}="a%20str"',
            b'map.{int}=1', b'map.{float}=1.0', b'map.none=',
            b'map.{}=5'
        ])
        parse_map = {
            'str': str,
            'int': int,
            'float': float
        }
        payload = Payload.from_bytes(data, parse_map)

        # WHEN
        parsed = payload.get_map('map')

        # THEN
        self.assertEqual({
            'bytes': b'bytes',
            'str': 'a str',
            'int': 1,
            'float': 1.0,
            'none': b''
        }, parsed)

    def test_get_map_not_a_struct(self):
        # GIVEN
        payload = Payload(key=b'value')

        # WHEN/THEN
        self.assertRaises(Error, payload.get_map, 'key')

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
            'str': 'str',
            'int': 1,
            'float': 1.0,
            'none': None
        }, existing)
        self.assertEqual({}, default)
        self.assertIsNone(missing)

    def test_get_dict_not_a_struct(self):
        # GIVEN
        payload = Payload(key=b'value')

        # WHEN/THEN
        self.assertRaises(Error, payload.get_dict, 'key')

    def test_struct_to_list_missing_length_indicator(self):
        # GIVEN
        payload = Payload.from_bytes(b'list.0=value')

        # WHEN/THEN
        self.assertRaises(Error, payload.struct_to_list, payload.data.get('list'))

    def test_struct_to_map_missing_length_indicator(self):
        # GIVEN
        payload = Payload.from_bytes(b'map.{key}=value')

        # WHEN/THEN
        self.assertRaises(Error, payload.struct_to_map, payload.data.get('map'))

    def test_personas_response(self):
        # GIVEN
        data = join_data([
            b'personas.[]=1', b'personas.0=yeas-yuwn-ep-lon', b'TXN=NuGetPersonas'
        ])
        parse_map = {
            MagicParseKey.index: str
        }
        payload = Payload.from_bytes(data, parse_map)

        # WHEN
        txn = payload.get_str('TXN')
        personas = payload.get_list('personas')

        # THEN
        self.assertEqual('NuGetPersonas', txn)
        self.assertEqual(['yeas-yuwn-ep-lon'], personas)

    def test_user_lookup_response(self):
        # GIVEN
        data = join_data([
            b'userInfo.0.namespace=PS3_SUB', b'userInfo.0.userId=891451503', b'TXN=LookupUserInfo',
            b'userInfo.0.xuid=8030785869539906380', b'userInfo.0.userName=sam707', b'userInfo.[]=1'
        ])
        parse_map = {
            'namespace': str,
            'userId': int,
            'xuid': int,
            'userName': str
        }
        payload = Payload.from_bytes(data, parse_map)

        # WHEN
        txn = payload.get_str('TXN')
        users = payload.get_list('userInfo')

        # THEN
        self.assertEqual('LookupUserInfo', txn)
        self.assertEqual([
            {'namespace': 'PS3_SUB', 'userId': 891451503, 'xuid': 8030785869539906380, 'userName': 'sam707'}
        ], users)

    def test_search_name_response(self):
        # GIVEN
        data = join_data([
            b'users.[]=1', b'users.0.id=1038690899', b'TXN=SearchOwners', b'users.0.name=Sam70786',
            b'nameSpaceId=XBL_SUB', b'users.0.type=1'
        ])
        parse_map = {
            'id': int,
            'name': str,
            'type': int
        }
        payload = Payload.from_bytes(data, parse_map)

        # WHEN
        txn = payload.get_str('TXN')
        namespace_id = payload.get_str('nameSpaceId')
        users = payload.get_list('users')

        # THEN
        self.assertEqual('SearchOwners', txn)
        self.assertEqual('XBL_SUB', namespace_id)
        self.assertEqual([
            {'id': 1038690899, 'name': 'Sam70786', 'type': 1}
        ], users)

    def test_stats_response(self):
        # GIVEN
        data = join_data([
            b'stats.1.key=losses', b'stats.[]=3', b'stats.2.value=16455.0', b'TXN=GetStats', b'stats.1.value=12006.0',
            b'stats.2.key=wins', b'stats.0.value=28461.0', b'stats.0.key=games'
        ])
        parse_map = {
            'key': str,
            'value': float
        }
        payload = Payload.from_bytes(data, parse_map)

        # WHEN
        txn = payload.get_str('TXN')
        stats = payload.get_list('stats')

        # THEN
        self.assertEqual('GetStats', txn)
        self.assertEqual([
            {'key': 'games', 'value': 28461.0},
            {'key': 'losses', 'value': 12006.0},
            {'key': 'wins', 'value': 16455.0}
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
        data = join_data([
            b'state=1', b'values.5.value=bGVtZW5rb29sAAAAAAAAAEWw6+8AAQkA', b'values.6.key=1055254420', b'TTL=0',
            b'values.3.value=TmlnaHRnYW1lcjI2NTcAAEWw6+AAAQMA', b'values.1.value=RGFya2xvcmQ5MHh4AAAAAEWw68QAAQAA',
            b'values.6.value=RmVsdEltcGFsYTY2ODkyAEWw7AcAAQYA', b'values.9.key=1055240877',
            b'values.2.value=RmF1eE5hbWVsZXNzAAAAAEWw68wAARkA', b'values.[]=10',
            b'values.8.value=TUlLODEzAAAAAAAAAAAAAEWw6+EAAQ4A', b'values.4.key=1048348626',
            b'values.7.value=UkVTUEFXTiBPTzcAAAAAAEWzfpIAARkA', b'values.9.value=RmF3YXogZ2IAAAAAAAAAAEWw7AAAARcA',
            b'values.7.key=992138898', b'lastModified="2023-09-22 19%3a42%3a57.0"', b'values.0.key=1055242182',
            b'values.5.key=1032604717', b'values.1.key=1055257806', b'values.3.key=1055257610',
            b'values.2.key=939363578', b'values.8.key=781949650', b'TXN=GetRecord',
            b'values.0.value=QnJhaW4gV3JvdWdodAAAAEWw6+8AARkA', b'values.4.value=UnlhbkRXeW5uZQAAAAAAAEWw7AkAAhkA'
        ])
        parse_map = {
            'key': int
        }
        payload = Payload.from_bytes(data, parse_map)

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
            {'key': 1055242182, 'value': b'QnJhaW4gV3JvdWdodAAAAEWw6+8AARkA'},
            {'key': 1055257806, 'value': b'RGFya2xvcmQ5MHh4AAAAAEWw68QAAQAA'},
            {'key': 939363578, 'value': b'RmF1eE5hbWVsZXNzAAAAAEWw68wAARkA'},
            {'key': 1055257610, 'value': b'TmlnaHRnYW1lcjI2NTcAAEWw6+AAAQMA'},
            {'key': 1048348626, 'value': b'UnlhbkRXeW5uZQAAAAAAAEWw7AkAAhkA'},
            {'key': 1032604717, 'value': b'bGVtZW5rb29sAAAAAAAAAEWw6+8AAQkA'},
            {'key': 1055254420, 'value': b'RmVsdEltcGFsYTY2ODkyAEWw7AcAAQYA'},
            {'key': 992138898, 'value': b'UkVTUEFXTiBPTzcAAAAAAEWzfpIAARkA'},
            {'key': 781949650, 'value': b'TUlLODEzAAAAAAAAAAAAAEWw6+EAAQ4A'},
            {'key': 1055240877, 'value': b'RmF3YXogZ2IAAAAAAAAAAEWw7AAAARcA'}
        ], values)

    def test_leaderboard_response(self):
        # GIVEN
        data = join_data([
            b'stats.4.addStats.2.value=1.1630278E7', b'stats.2.owner=959040406', b'stats.4.addStats.1.key=kills',
            b'stats.0.addStats.1.key=kills', b'stats.4.addStats.0.value=151531.0', b'stats.2.addStats.2.key=score',
            b'stats.0.value=2.4056603E7', b'stats.0.addStats.[]=4', b'stats.1.addStats.0.value=292627.0',
            b'stats.0.addStats.0.value=988609.0', b'stats.2.rank=3', b'stats.0.addStats.3.value=6.6336188019E7',
            b'stats.1.rank=2', b'stats.4.name="K5Q Blan"', b'stats.2.addStats.1.key=kills', b'stats.3.addStats.1.key=kills',
            b'stats.2.name="o lNiiNJA"', b'stats.3.owner=925212106', b'stats.4.rank=5', b'stats.4.addStats.[]=4',
            b'stats.2.addStats.3.key=time', b'stats.3.addStats.3.key=time', b'stats.0.rank=1', b'stats.0.addStats.2.key=score',
            b'stats.3.addStats.2.key=score', b'stats.2.addStats.0.value=127087.0', b'stats.4.addStats.3.key=time',
            b'TXN=GetTopNAndStats', b'stats.1.addStats.[]=4', b'stats.3.addStats.3.value=2.5479985997E7',
            b'stats.4.value=1.1630278E7', b'stats.2.addStats.0.key=deaths', b'stats.3.addStats.2.value=1.2270119E7',
            b'stats.3.value=1.2270119E7', b'stats.4.addStats.3.value=2.2121341986E7', b'stats.1.addStats.3.key=time',
            b'stats.3.addStats.0.value=180779.0', b'stats.1.owner=853198764', b'stats.[]=5', b'stats.1.value=1.553427E7',
            b'stats.1.addStats.1.key=kills', b'stats.2.addStats.1.value=636392.0',
            b'stats.1.addStats.3.value=4.3991928017E7', b'stats.0.owner=905760050', b'stats.0.addStats.2.value=2.4056603E7',
            b'stats.0.addStats.3.key=time', b'stats.0.addStats.0.key=deaths', b'stats.2.addStats.2.value=1.3002937E7',
            b'stats.4.addStats.1.value=568653.0', b'stats.2.value=1.3002937E7', b'stats.1.addStats.0.key=deaths',
            b'stats.3.addStats.0.key=deaths', b'stats.3.name=Schmittepitter', b'stats.0.addStats.1.value=1082418.0',
            b'stats.2.addStats.[]=4', b'stats.3.addStats.1.value=572390.0', b'stats.1.name="BONE 815"',
            b'stats.4.addStats.0.key=deaths', b'stats.3.rank=4', b'stats.1.addStats.2.key=score', b'stats.0.name=daddyo21252',
            b'stats.4.addStats.2.key=score', b'stats.3.addStats.[]=4', b'stats.1.addStats.1.value=738204.0',
            b'stats.2.addStats.3.value=2.1566129983E7', b'stats.4.owner=987817822', b'stats.1.addStats.2.value=1.553427E7'
        ])
        parse_map = {
            'owner': int,
            'name': str,
            'rank': int,
            'value': float,
            'key': str
        }
        payload = Payload.from_bytes(data, parse_map)

        # WHEN
        txn = payload.get('TXN')
        stats = payload.get_list('stats')

        # THEN
        self.assertEqual(b'GetTopNAndStats', txn)
        self.assertEqual([
            {
                'owner': 905760050,
                'name': 'daddyo21252',
                'rank': 1,
                'value': 2.4056603E7,
                'addStats': [
                    {'key': 'deaths', 'value': 988609.0},
                    {'key': 'kills', 'value': 1082418.0},
                    {'key': 'score', 'value': 2.4056603E7},
                    {'key': 'time', 'value': 6.6336188019E7},
                ]
            },
            {
                'owner': 853198764,
                'name': 'BONE 815',
                'rank': 2,
                'value': 1.553427E7,
                'addStats': [
                    {'key': 'deaths', 'value': 292627.0},
                    {'key': 'kills', 'value': 738204.0},
                    {'key': 'score', 'value': 1.553427E7},
                    {'key': 'time', 'value': 4.3991928017E7},
                ]
            },
            {
                'owner': 959040406,
                'name': 'o lNiiNJA',
                'rank': 3,
                'value': 1.3002937E7,
                'addStats': [
                    {'key': 'deaths', 'value': 127087.0},
                    {'key': 'kills', 'value': 636392.0},
                    {'key': 'score', 'value': 1.3002937E7},
                    {'key': 'time', 'value': 2.1566129983E7},
                ]
            },
            {
                'owner': 925212106,
                'name': 'Schmittepitter',
                'rank': 4,
                'value': 1.2270119E7,
                'addStats': [
                    {'key': 'deaths', 'value': 180779.0},
                    {'key': 'kills', 'value': 572390.0},
                    {'key': 'score', 'value': 1.2270119E7},
                    {'key': 'time', 'value': 2.5479985997E7},
                ]
            },
            {
                'owner': 987817822,
                'name': 'K5Q Blan',
                'rank': 5,
                'value': 1.1630278E7,
                'addStats': [
                    {'key': 'deaths', 'value': 151531.0},
                    {'key': 'kills', 'value': 568653.0},
                    {'key': 'score', 'value': 1.1630278E7},
                    {'key': 'time', 'value': 2.2121341986E7},
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
