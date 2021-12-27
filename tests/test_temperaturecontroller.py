from functools import partial
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
        self.speeds = interpolate_temps({
            "temps": "30, 55 | 50, 80",
            'minimumSpeed': self.minimum_speed,
            'maximumSpeed': self.maximum_speed
        })
        self.controller = TemperatureController([self.dummy_input], [self.dummy_output], self.speeds)
        self.lerp = partial(lerp, input_min=0, input_max=255, output_min=0, output_max=100)

    def _run_loop(self, times=1):
        for _ in range(times):
            self.controller.run()
            for o in self.controller.apply_candidates():
                o.apply()

    def test_run(self):
        self.controller.enable()
        self.dummy_input.set_value(0)
        self._run_loop(2)
        self.assertAlmostEqual(self.minimum_speed, int(self.lerp(self.dummy_output.speed)), delta=2)

        self.dummy_input.set_value(100)
        self._run_loop(128)

        self.assertAlmostEqual(self.maximum_speed, int(self.lerp(self.dummy_output.speed)), delta=2)

        self.dummy_input.set_value(55)
        self._run_loop(128)

        self.assertAlmostEqual(50, int(self.lerp(self.dummy_output.speed)), delta=2)

    def test_enable(self):
        self.controller.enable()
        for dev in self.controller.outputs:
            self.assertTrue(dev.enabled)

    def test_disable(self):
        self.controller.enable()
        self.controller.disable()
        for dev in self.controller.outputs:
            self.assertFalse(dev.enabled)
