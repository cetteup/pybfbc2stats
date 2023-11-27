import unittest

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
