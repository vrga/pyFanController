from unittest import TestCase

from pyfc.common import DummyOutput


class TestOutputDevice(TestCase):
    def setUp(self) -> None:
        self.test_output = DummyOutput()

    def test_enable(self):
        self.test_output.enable()
        self.assertTrue(self.test_output.enabled)

    def test_set_speed(self):
        self.test_output.set_value(100)
        self.test_output.enable()
        self.assertTrue(self.test_output.enabled)
        self.test_output.set_value(100)
        self.assertAlmostEqual(100.0, self.test_output.values.mean())

    def test_disable(self):
        self.test_output.enable()
        self.test_output.disable()
        self.assertFalse(self.test_output.enabled)
