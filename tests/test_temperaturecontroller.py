from unittest import TestCase

from pyfc.common import DummyInput, DummyOutput, lerp
from pyfc.deviceloader import interpolate_temps
from pyfc.temperaturecontroller import TemperatureController


class TestTemperatureController(TestCase):
    def setUp(self) -> None:
        self.dummy_input = DummyInput()
        self.dummy_output = DummyOutput()
        self.minimum_speed = 20
        self.maximum_speed = 100
        self.speeds = interpolate_temps({"temps": "30, 55 | 50, 80", 'minimumSpeed': self.minimum_speed, 'maximumSpeed': self.maximum_speed})
        self.controller = TemperatureController([self.dummy_input], [self.dummy_output], self.speeds)

    def test_run(self):
        self.controller.enable()
        self.dummy_input.set_temp(0)
        self.controller.run()
        self.assertAlmostEqual(self.minimum_speed, int(lerp(self.dummy_output.speed, 0, 255, 0, 100)), delta=2)

        self.dummy_input.set_temp(100)
        self.controller.run()
        self.assertAlmostEqual(self.maximum_speed, int(lerp(self.dummy_output.speed, 0, 255, 0, 100)), delta=2)

        self.dummy_input.set_temp(55)
        self.controller.run()
        self.assertAlmostEqual(50, int(lerp(self.dummy_output.speed, 0, 255, 0, 100)), delta=2)

    def test_enable(self):
        self.controller.enable()
        for dev in self.controller.outputs:
            self.assertTrue(dev.enabled)

    def test_disable(self):
        self.controller.enable()
        self.controller.disable()
        for dev in self.controller.outputs:
            self.assertFalse(dev.enabled)