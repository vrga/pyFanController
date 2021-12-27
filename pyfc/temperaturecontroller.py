import logging
from typing import List, Union, Iterable

from .common import InputDevice, OutputDevice, Controller, lerp, mean

log = logging.getLogger(__name__)


class TemperatureController(Controller):
    """
        raw temperature controller
    """

    def __init__(self, input_devices: Iterable[InputDevice], output_devices: Iterable[OutputDevice], speeds: List[int]):
        """
        :param input_devices: Input device from which we take the temperature.
        :param output_devices: Output device to which we set the speed
        :param speeds: tuple of speeds to which we set it.
        """
        self.inputs = [d for d in input_devices if d]
        self.outputs = [d for d in output_devices if d]
        self.speeds = speeds

    def get_speed(self, temp: Union[float, int]):
        temp = int(temp)
        try:
            speed = self.speeds[temp]
        except IndexError:
            if temp >= len(self.speeds):
                speed = self.speeds[-1]
            else:
                speed = self.speeds[0]
        finally:
            log.debug('temperature %s°C, speed: %s%%', temp, int(lerp(speed, 0, 255, 0, 100)))
            return speed

    def run(self):
        """
            method which runs the thing.
            If reported temperature is 0, take previous temp
        """
        try:
            temp = mean([input_dev.get_value() for input_dev in self.inputs])
            speed = self.get_speed(temp)
        except ValueError:
            speed = 128

        for output_dev in self.outputs:
            output_dev.set_value(speed)

    def apply_candidates(self):
        return self.outputs

    def enable(self):
        for output_dev in self.outputs:
            output_dev.enable()

    def disable(self):
        for output_dev in self.outputs:
            output_dev.disable()

    def valid(self) -> bool:
        return bool(self.inputs and self.outputs and self.speeds)

    def __del__(self):
        self.disable()
