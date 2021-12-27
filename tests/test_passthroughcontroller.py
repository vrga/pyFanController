from unittest import TestCase

from pyfc.common import DummyInput, DummyOutput, PassthroughController


class TestPassthroughController(TestCase):
    def setUp(self) -> None:
        self.dummy_input = DummyInput()
        self.dummy_output = DummyOutput()
        self.controller = PassthroughController([self.dummy_input], [self.dummy_output])

    def _run_loop(self, times=1):
        for _ in range(times):
            self.controller.run()

    def test_run(self):
        self.controller.enable()
        self.dummy_input.set_value(0)
        self._run_loop()
        self.assertEqual(0, self.dummy_output.speed)

        self.dummy_input.set_value(100)
        self._run_loop(32)
        self.assertEqual(100, self.dummy_output.speed)

        self.dummy_input.set_value(55)
        self._run_loop(32)
        self.assertEqual(55, self.dummy_output.speed)

