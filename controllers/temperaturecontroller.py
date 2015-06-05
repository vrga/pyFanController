import logging

from ..devicecontainers.inputdevice import InputDevice
from ..devicecontainers.outputdevice import OutputDevice


class TemperatureController(object):
    """
        raw temperature controller
    """

    def __init__(self, input_device, output_device, speeds):
        """
        :param input_device: Input device from which we take the temperature.
        :type input_device: InputDevice
        :param output_device: Output device to which we set the speed
        :type output_device: OutputDevice
        :param speeds: tuple of speeds to which we set it.
        :type speeds: tuple
        """
        self.input = input_device
        self.output = output_device
        self.speeds = speeds
        self.temp = 0
        self.speed = 0

    def run(self):
        """
            method which runs the thing.
            If reported temperature is 0, take previous temp
        """
        temp = self.input.get_temp()
        if temp != 0:
            self.temp = temp
        self.speed = self.speeds[self.temp]
        logging.debug('temperature %s°C, speed: %s%%', self.temp, self.speed)
        self.output.set_speed(self.speed)

    def enable(self):
        self.output.enable()

    def disable(self):
        self.output.disable()

    def __del__(self):
        self.disable()
