from unittest import TestCase

from pyfc.common import DummyInput


class TestInputDevice(TestCase):
    def setUp(self) -> None:
        self.test_input = DummyInput()

    def test_get_temp(self):
        self.assertEqual(0, self.test_input.get_value(), 'Value should be 0!')
        self.test_input.set_value(90)
        self.assertEqual(90, self.test_input.get_value(), 'Temperature should be 90!')

    def test_set_temp(self):
        self.test_input.set_value(90)
        self.assertEqual(90, self.test_input.get_value(), 'Temperature should be 90!')

