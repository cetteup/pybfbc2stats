import unittest

from pybfbc2stats import FeslClient, Platform, Error


class FeslClientTest(unittest.TestCase):
    def test_format_dogtags_response(self):
        # GIVEN
        parsed_response = {
            1234567890: b'some_player_name\x00\xc0GD\x01\x00\x02\x00\x03\x002\x00'
        }

        # WHEN
        formatted = FeslClient.format_dogtags_response(parsed_response, Platform.pc)

        # THEN
        self.assertEqual(1, len(formatted))
        self.assertEqual(1234567890, formatted[0]['userId'])
        self.assertEqual('some_player_name', formatted[0]['userName'])
        self.assertEqual(1268179200.0, formatted[0]['timestamp'])
        self.assertEqual(50, formatted[0]['rank'])
        self.assertEqual(1, formatted[0]['gold'])
        self.assertEqual(2, formatted[0]['silver'])
        self.assertEqual(3, formatted[0]['bronze'])
        self.assertEqual(6, formatted[0]['dogtags'])
        self.assertEqual(parsed_response[1234567890], formatted[0]['raw'])

    def test_format_dogtags_response_console(self):
        # GIVEN
        parsed_response = {
            1234567890: b'some_player_nameDG\xc0\x00\x00\x01\x00\x02\x00\x032\x00'
        }

        # WHEN
        formatted = FeslClient.format_dogtags_response(parsed_response, Platform.ps3)

        # THEN
        self.assertEqual(1, len(formatted))
        self.assertEqual(1268179200.0, formatted[0]['timestamp'])
        self.assertEqual(50, formatted[0]['rank'])
        self.assertEqual(1, formatted[0]['gold'])
        self.assertEqual(2, formatted[0]['silver'])
        self.assertEqual(3, formatted[0]['bronze'])
        self.assertEqual(6, formatted[0]['dogtags'])

    def test_format_dogtags_response_remove_name_null_bytes(self):
        # GIVEN
        parsed_response = {
            1234567890: b'player_name\x00\x00\x00\x00\x00DG\xc0\x00\x00\x01\x00\x02\x00\x032\x00'
        }

        # WHEN
        formatted = FeslClient.format_dogtags_response(parsed_response, Platform.ps3)

        # THEN
        self.assertEqual(1, len(formatted))
        self.assertEqual('player_name', formatted[0]['userName'])

    def test_format_dogtags_response_replace_name_utf8_errors(self):
        # GIVEN
        parsed_response = {
            1234567890: b'\xac\x1d5\x08Dvil07\x00\x00\x00\x00\x00\x00\x00\xc0GD\x01\x00\x02\x00\x03\x002\x00'
        }

        # WHEN
        formatted = FeslClient.format_dogtags_response(parsed_response, Platform.ps3)

        # THEN
        self.assertEqual(1, len(formatted))
        self.assertEqual('�\x1d5\x08Dvil07', formatted[0]['userName'])

    def test_format_dogtags_response_bad_company(self):
        # GIVEN
        parsed_response = {
            1234567890: b'some_player_name\x00\xc0GD\x06\x002\x00'
        }

        # WHEN
        formatted = FeslClient.format_dogtags_response(parsed_response, Platform.pc)

        # THEN
        self.assertEqual(1, len(formatted))
        self.assertEqual(1234567890, formatted[0]['userId'])
        self.assertEqual('some_player_name', formatted[0]['userName'])
        self.assertEqual(1268179200.0, formatted[0]['timestamp'])
        self.assertEqual(50, formatted[0]['rank'])
        self.assertNotIn('gold', formatted[0].keys())
        self.assertNotIn('silver', formatted[0].keys())
        self.assertNotIn('bronze', formatted[0].keys())
        self.assertEqual(6, formatted[0]['dogtags'])
        self.assertEqual(parsed_response[1234567890], formatted[0]['raw'])

    def test_format_dogtags_response_invalid_record(self):
        # GIVEN
        parsed_response = {
            1234567890: b'some_player_name\x00\xc0GD2\x00'
        }

        # WHEN/THEN
        self.assertRaises(Error, FeslClient.format_dogtags_response, parsed_response, Platform.pc)
