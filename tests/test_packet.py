import unittest

from pybfbc2stats import Error
from pybfbc2stats.constants import FeslTransmissionType, TheaterTransmissionType
from pybfbc2stats.packet import FeslPacket, TheaterPacket
from pybfbc2stats.payload import Payload


class FeslPacketTest(unittest.TestCase):
    def test_build(self):
        # GIVEN
        header_stub = b'fsys'
        body_data = b'TXN=Hello'
        transmission_type = FeslTransmissionType.SinglePacketRequest
        tid = 1

        # WHEN
        packet = FeslPacket.build(header_stub, body_data, transmission_type, tid)

        # THEN
        expected = FeslPacket(b'fsys\xc0\x00\x00\x01\x00\x00\x00\x16', b'TXN=Hello\x00')
        self.assertEqual(expected, packet)
        self.assertIsNone(packet.validate())

    def test_build_no_tid(self):
        # GIVEN
        header_stub = b'fsys'
        body_data = b'TXN=MemCheck\nresult='
        transmission_type = FeslTransmissionType.SinglePacketResponse

        # WHEN
        packet = FeslPacket.build(header_stub, body_data, transmission_type)

        # THEN
        expected = FeslPacket(b'fsys\x80\x00\x00\x00\x00\x00\x00!', b'TXN=MemCheck\nresult=\x00')
        self.assertEqual(expected, packet)
        self.assertIsNone(packet.validate())

    def test_to_bytes(self):
        # GIVEN
        header = b'fsys\x80\x00\x00\x00\x00\x00\x00"'
        body = b'TXN=MemCheck\nresult=\n\x00'
        packet = FeslPacket(header, body)

        # WHEN
        as_bytes = bytes(packet)

        # THEN
        self.assertEqual(header + body, as_bytes)

    def test_validate_header(self):
        # GIVEN
        packet = FeslPacket(b'fsys\x80\x00\x00\x00\x00\x00\x00"', b'TXN=MemCheck\nresult=\n\x00')

        # WHEN/THEN
        self.assertIsNone(packet.validate_header())

    def test_validate_header_incorrect_length(self):
        # GIVEN
        packet = FeslPacket(b'fsys\x80\x00\x00\x00', b'TXN=MemCheck\nresult=\n\x00')

        # WHEN/THEN
        self.assertRaises(Error, packet.validate_header)

    def test_validate_header_zero_length_body_indicator(self):
        # GIVEN
        packet = FeslPacket(b'fsys\x80\x00\x00\x00\x00\x00\x00\x00', b'TXN=MemCheck\nresult=\n\x00')

        # WHEN/THEN
        self.assertRaises(Error, packet.validate_header)

    def test_validate_header_invalid_type(self):
        # GIVEN
        packet = FeslPacket(b'none\x80\x00\x00\x00\x00\x00\x00"', b'TXN=MemCheck\nresult=\n\x00')

        # WHEN/THEN
        self.assertRaises(Error, packet.validate_header)

    def test_validate_header_invalid_packet_count_indicator(self):
        # GIVEN
        packet = FeslPacket(b'fsys\x99\x00\x00\x00\x00\x00\x00"', b'TXN=MemCheck\nresult=\n\x00')

        # WHEN/THEN
        self.assertRaises(Error, packet.validate_header)

    def test_validate_body(self):
        # GIVEN
        packet = FeslPacket(b'fsys\x80\x00\x00\x00\x00\x00\x00"', b'TXN=MemCheck\nresult=\n\x00')

        # WHEN/THEN
        self.assertIsNone(packet.validate_body())

    def test_validate_body_length_mismatch(self):
        # GIVEN
        packet = FeslPacket(b'fsys\x80\x00\x00\x00\x00\x00\x00"', b'TXN=MemCheck\n\x00')

        # WHEN/THEN
        self.assertRaises(Error, packet.validate_body)

    def test_set_get_tid(self):
        # GIVEN
        given_tid = 1
        packet = FeslPacket(b'fsys\xc0\x00\x00\x00\x00\x00\x00"', b'TXN=MemCheck\nresult=\n\x00')
        self.assertIsNone(packet.validate())

        # WHEN
        packet.set_tid(given_tid)

        # AND
        tid = packet.get_tid()

        self.assertEqual(given_tid, tid)

    def test_indicated_body_length(self):
        # GIVEN
        expected_length = 22
        packet = FeslPacket(b'fsys\x80\x00\x00\x00\x00\x00\x00"', b'TXN=MemCheck\nresult=\n\x00')
        self.assertIsNone(packet.validate())

        # WHEN
        body_length = packet.indicated_body_length()

        # THEN
        self.assertEqual(expected_length, body_length)

    def test_get_payload(self):
        # GIVEN
        data = b'TXN=MemCheck\nresult='
        packet = FeslPacket(b'fsys\x80\x00\x00\x00\x00\x00\x00!', data + b'\x00')
        self.assertIsNone(packet.validate())

        # WHEN
        payload = packet.get_payload()

        # THEN
        self.assertEqual(Payload.from_bytes(data), payload)

    def test_get_payload_parsed(self):
        # GIVEN
        data = b'TXN=MemCheck\nresult='
        parse_map = {
            'TXN': str,
            'result': str
        }
        packet = FeslPacket(b'fsys\x80\x00\x00\x00\x00\x00\x00!', data + b'\x00')
        self.assertIsNone(packet.validate())

        # WHEN
        payload = packet.get_payload(parse_map)

        # THEN
        self.assertEqual(Payload.from_bytes(data, parse_map), payload)

    def test_get_data(self):
        # GIVEN
        expected_data = b'TXN=MemCheck\nresult=\n'
        packet = FeslPacket(b'fsys\x80\x00\x00\x00\x00\x00\x00"', expected_data + b'\x00')
        self.assertIsNone(packet.validate())

        # WHEN
        data = packet.get_data()

        # THEN
        self.assertEqual(expected_data, data)

    def test_get_data_lines(self):
        # GIVEN
        expected_data_lines = [b'TXN=MemCheck', b'result=', b'']
        packet = FeslPacket(b'fsys\x80\x00\x00\x00\x00\x00\x00"', b'\n'.join(expected_data_lines) + b'\x00')
        self.assertIsNone(packet.validate())

        # WHEN
        data_lines = packet.get_data_lines()

        # THEN
        self.assertEqual(expected_data_lines, data_lines)


class TheaterPacketTest(unittest.TestCase):
    def test_build(self):
        # GIVEN
        header_stub = b'GDAT'
        body_data = b'LID=257\nGID=123456'
        transmission_type = TheaterTransmissionType.Request
        tid = 1

        # WHEN
        packet = TheaterPacket.build(header_stub, body_data, transmission_type, tid)

        # THEN
        expected = TheaterPacket(b'GDAT@\x00\x00\x00\x00\x00\x00%', b'LID=257\nGID=123456\nTID=1\x00')
        self.assertEqual(expected, packet)
        self.assertIsNone(packet.validate())

    def test_build_no_tid(self):
        # GIVEN
        header_stub = b'PING'
        body_data = b'TID=0'
        transmission_type = TheaterTransmissionType.OKResponse

        # WHEN
        packet = TheaterPacket.build(header_stub, body_data, transmission_type)

        # THEN
        expected = TheaterPacket(b'PING\x00\x00\x00\x00\x00\x00\x00\x12', b'TID=0\x00')
        self.assertEqual(expected, packet)
        self.assertIsNone(packet.validate())

    def test_to_bytes(self):
        # GIVEN
        header = b'GDAT@\x00\x00\x00\x00\x00\x00&'
        body = b'LID=257\nGID=123456\nTID=1\n\x00'
        packet = TheaterPacket(header, body)

        # WHEN
        as_bytes = bytes(packet)

        # THEN
        self.assertEqual(header + body, as_bytes)

    def test_validate_header_request(self):
        # GIVEN
        packet = TheaterPacket(b'GDAT@\x00\x00\x00\x00\x00\x00&', b'LID=257\nGID=123456\nTID=1\n\x00')

        # WHEN/THEN
        self.assertIsNone(packet.validate_header())

    def test_validate_header_response(self):
        # GIVEN
        packet = TheaterPacket(b'GDAT\x00\x00\x00\x00\x00\x00\x00(', b'JP=0\nHN=bfbc2.server.p\nTID=1\x00')

        # WHEN/THEN
        self.assertIsNone(packet.validate_header())

    def test_validate_header_error(self):
        # GIVEN
        packet = TheaterPacket(b'GDATngam\x00\x00\x00\x12', b'TID=3\x00')

        # WHEN/THEN
        self.assertIsNone(packet.validate_header())

    def test_validate_header_incorrect_length(self):
        # GIVEN
        packet = TheaterPacket(b'GDAT@\x00\x00\x00', b'TXN=MemCheck\nresult=\n\x00')

        # WHEN/THEN
        self.assertRaises(Error, packet.validate_header)

    def test_validate_header_zero_length_body_indicator(self):
        # GIVEN
        packet = TheaterPacket(b'GDAT@\x00\x00\x00\x00\x00\x00\x00', b'TXN=MemCheck\nresult=\n\x00')

        # WHEN/THEN
        self.assertRaises(Error, packet.validate_header)

    def test_validate_invalid_type(self):
        # GIVEN
        packet = TheaterPacket(b'none@\x00\x00\x00\x00\x00\x00&', b'LID=257\nGID=123456\nTID=1\x00')

        # WHEN/THEN
        self.assertRaises(Error, packet.validate_header)

    def test_validate_invalid_status_indicator(self):
        # GIVEN
        packet = TheaterPacket(b'GDAT\x01\x01\x01\x01\x00\x00\x00%', b'LID=257\nGID=123456\nTID=1\x00')

        # WHEN/THEN
        self.assertRaises(Error, packet.validate_header)

    def test_validate_body(self):
        # GIVEN
        packet = TheaterPacket(b'GDAT@\x00\x00\x00\x00\x00\x00&', b'LID=257\nGID=123456\nTID=1\n\x00')

        # WHEN/THEN
        self.assertIsNone(packet.validate_body())

    def test_validate_body_length_mismatch(self):
        # GIVEN
        packet = TheaterPacket(b'GDAT@\x00\x00\x00\x00\x00\x00&', b'LID=257\nTID=1\n\x00')

        # WHEN/THEN
        self.assertRaises(Error, packet.validate_body)

    def test_set_get_tid(self):
        # GIVEN
        given_tid = 1
        packet = TheaterPacket(b'GDAT@\x00\x00\x00\x00\x00\x00 ', b'LID=257\nGID=123456\n\x00')
        self.assertIsNone(packet.validate())

        # WHEN
        packet.set_tid(given_tid)

        # AND
        tid = packet.get_tid()

        self.assertEqual(given_tid, tid)

    def test_get_tid_no_tid(self):
        # GIVEN
        packet = TheaterPacket(b'GDAT@\x00\x00\x00\x00\x00\x00 ', b'LID=257\nGID=123456\n\x00')
        self.assertIsNone(packet.validate())

        # WHEN
        tid = packet.get_tid()

        self.assertEqual(0, tid)

    def test_indicated_body_length(self):
        # GIVEN
        expected_length = 26
        packet = TheaterPacket(b'GDAT@\x00\x00\x00\x00\x00\x00&', b'LID=257\nGID=123456\nTID=1\n\x00')
        self.assertIsNone(packet.validate())

        # WHEN
        body_length = packet.indicated_body_length()

        # THEN
        self.assertEqual(expected_length, body_length)

    def test_get_data(self):
        # GIVEN
        expected_data = b'LID=257\nGID=123456\nTID=1\n'
        packet = TheaterPacket(b'GDAT@\x00\x00\x00\x00\x00\x00&', expected_data + b'\x00')
        self.assertIsNone(packet.validate())

        # WHEN
        data = packet.get_data()

        # THEN
        self.assertEqual(expected_data, data)

    def test_get_data_lines(self):
        # GIVEN
        expected_data_lines = [b'LID=257', b'GID=123456', b'TID=1', b'']
        packet = TheaterPacket(b'GDAT@\x00\x00\x00\x00\x00\x00&', b'\n'.join(expected_data_lines) + b'\x00')
        self.assertIsNone(packet.validate())

        # WHEN
        data_lines = packet.get_data_lines()

        # THEN
        self.assertEqual(expected_data_lines, data_lines)
