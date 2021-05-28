from unittest import TestCase

from pyfc.common import DummyOutput


class TestOutputDevice(TestCase):
    def setUp(self) -> None:
        self.test_output = DummyOutput()

    def test_enable(self):
        self.test_output.enable()
        self.assertTrue(self.test_output.enabled)

    def test_set_speed(self):
        self.assertFalse(self.test_output.set_speed(100))
        self.test_output.enable()
        self.assertTrue(self.test_output.enabled)
        self.assertTrue(self.test_output.set_speed(100))

    def test_disable(self):
        self.test_output.enable()
        self.test_output.disable()
        self.assertFalse(self.test_output.enabled)
