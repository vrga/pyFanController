import logging
from typing import List

from .common import InputDevice, OutputDevice, lerp, mean

log = logging.getLogger(__name__)


class TemperatureController:
    """
        raw temperature controller
    """

    def __init__(self, input_devices: List[InputDevice], output_devices: List[OutputDevice], speeds: List[int]):
        """
        :param input_devices: Input device from which we take the temperature.
        :param output_devices: Output device to which we set the speed
        :param speeds: tuple of speeds to which we set it.
        """
        self.inputs = input_devices
        self.outputs = output_devices
        self.speeds = speeds
        self.temp = 0
        self.speed = 0

    def run(self):
        """
            method which runs the thing.
            If reported temperature is 0, take previous temp
        """
        temp = mean([input_dev.get_temp() for input_dev in self.inputs])
        if temp != 0:
            self.temp = temp
        self.speed = self.speeds[self.temp]
        log.debug('temperature %s°C, speed: %s%%', self.temp, int(lerp(self.speed, 0, 255, 0, 100)))
        for output_dev in self.outputs:
            output_dev.set_speed(self.speed)

    def enable(self):
        for output_dev in self.outputs:
            output_dev.enable()

    def disable(self):
        for output_dev in self.outputs:
            output_dev.disable()

    def __del__(self):
        self.disable()
