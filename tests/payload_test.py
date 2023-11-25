import unittest

from pybfbc2stats.payload import Payload, FeslPayload


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

    def test_set(self):
        # GIVEN
        payload = Payload()

        # WHEN
        payload.set('bytes', b'bytes')
        payload.set('str', 'str')
        payload.set('int', 1)
        payload.set('float', 1.0)
        payload.set('none', None)

        # THEN
        self.assertEqual(b'bytes', payload.data.get('bytes'))
        self.assertEqual(b'str', payload.data.get('str'))
        self.assertEqual(b'1', payload.data.get('int'))
        self.assertEqual(b'1.0', payload.data.get('float'))
        self.assertEqual(b'', payload.data.get('none'))
        self.assertEqual(5, len(payload.data))

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


class FeslPayloadTest(unittest.TestCase):
    def test_set_list(self):
        # GIVEN
        payload = FeslPayload(existing='existing')
        items = [b'bytes', 'str', 1, 1.0, None]

        # WHEN
        payload.set_list(items, 'prefix')

        # THEN
        self.assertEqual(b'existing', payload.data.get('existing'))
        self.assertEqual(b'bytes', payload.data.get('prefix.0'))
        self.assertEqual(b'str', payload.data.get('prefix.1'))
        self.assertEqual(b'1', payload.data.get('prefix.2'))
        self.assertEqual(b'1.0', payload.data.get('prefix.3'))
        self.assertEqual(b'', payload.data.get('prefix.4'))
        self.assertEqual(b'5', payload.data.get('prefix.[]'))
        self.assertEqual(7, len(payload.data))

    def test_set_list_dicts(self):
        # GIVEN
        payload = FeslPayload(existing='existing')
        items = [
            {
                'bytes': b'bytes 1',
                'str': 'str 1',
                'int': 1,
                'float': 1.0,
                'none': None
            },
            {
                'bytes': b'bytes 2',
                'str': 'str 2',
                'int': 2,
                'float': 2.0,
                'none': None
            }
        ]

        # WHEN
        payload.set_list(items, 'prefix')

        # THEN
        self.assertEqual(b'existing', payload.data.get('existing'))
        self.assertEqual(b'bytes 1', payload.data.get('prefix.0.bytes'))
        self.assertEqual(b'str 1', payload.data.get('prefix.0.str'))
        self.assertEqual(b'1', payload.data.get('prefix.0.int'))
        self.assertEqual(b'1.0', payload.data.get('prefix.0.float'))
        self.assertEqual(b'', payload.data.get('prefix.0.none'))
        self.assertEqual(b'bytes 2', payload.data.get('prefix.1.bytes'))
        self.assertEqual(b'str 2', payload.data.get('prefix.1.str'))
        self.assertEqual(b'2', payload.data.get('prefix.1.int'))
        self.assertEqual(b'2.0', payload.data.get('prefix.1.float'))
        self.assertEqual(b'', payload.data.get('prefix.1.none'))
        self.assertEqual(b'2', payload.data.get('prefix.[]'))
        self.assertEqual(12, len(payload.data))
