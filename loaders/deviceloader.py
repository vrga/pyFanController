import logging

from numpy import interp

from ..controllers.temperaturecontroller import TemperatureController
from ..devicecontainers.lmsensorsinputfile import LMSensorsInputFile
from ..devicecontainers.hddtemp import HDDTemp
from ..devicecontainers.lmsensorsoutputfile import LMSensorsOutputFile
from ..devicecontainers.serialoutput import SerialOutput


class DeviceLoader(object):
    """
        Class to get configurations and build device objects from those configs.
    """

    def __init__(self, config):
        self.config = config
        self.serial = config.get('base').getboolean('serial')
        self.hddtemp = config.get('base').getboolean('hddtemp')

    def create_devices(self):
        """
        creates all device from configured ones
        :return:
        :rtype: dict[str, TemperatureController]
        """
        devices = self.config.get('base').get('devices').split('. ')

        if not devices:
            raise ValueError('No devices enabled, please enable at least one.')

        return {device: self.create_device(device) for device in devices}

    def create_device(self, device_name):
        """
        creates device from name
        :param device_name:
        :type device_name: str
        :return:
        :rtype: TemperatureController
        """
        logging.debug('Assembling device: %s', device_name)
        data = self.config.get(device_name)

        if data.get('inputType') == 'componentTemp':
            prefix = data.get('tempMonDevicePathPrefix')
            input_device = LMSensorsInputFile(tuple(prefix.join(path) for path in data.get('temperatureMonitor')))
        elif self.hddtemp and data.get('inputType') == 'hddtemp':
            input_device = HDDTemp()
        else:
            raise ValueError('No Input device created, check the configuration!')

        if data.get('outputType') == 'fanPWM':
            prefix = data.get('mainDevicePathPrefix')
            output_device = LMSensorsOutputFile(prefix.join(data.get('device')), prefix.join(data.get('outputEnabler')))
        elif self.serial and data.get('outputType') == 'serial':
            output_device = SerialOutput(int(data.get('device')))
        else:
            raise ValueError('No output device created, check the configuration!')

        speeds = self.interpolate_temps(data)

        device = TemperatureController(input_device, output_device, speeds)

        if not device:
            return None
        else:
            return device

    def interpolate_temps(self, device_data):
        """
        takes config data for device, spits out a 100 entries long tuple for
        all the possible temperature->speed combinations possible for the set parameters.

        TODO: verify that all sets are upward sequences.
        :param device_data: configuration data for device
        """
        temps = device_data.get('temps')
        # split string and turn it all to int.
        temp_ranges = [[int(item.strip()) for item in temp.split('|')] for temp in temps.split(', ')]

        """
        determine first and last temperature
        and treat them as minimum and maximum of the ranges
        temp > max = maximum fan speed
        temp < min = minimum fan speed
        """
        first = temp_ranges.pop(0)
        first.append(int(device_data.get('minimumSpeed')))
        last = temp_ranges.pop()
        last.append(int(device_data.get('maximumSpeed')))

        temp_ranges.insert(0, first)
        temp_ranges.append(last)

        speeds = []
        """
        speed value determination...
        TODO: Try to simplify this? I've lost more time on this tidbit than any other...
        """
        previous_range = 1
        previous_max_speed = first[1]
        for ranges in temp_ranges:
            current_range = ranges[0]
            current_max_speed = ranges[1]

            values = interp(
                range(previous_range, current_range),  # current temperature steps
                [previous_range, current_range],  # previous max temp range, current max temp range
                [previous_max_speed, current_max_speed]  # previous max speed, current max speed
            )

            speeds.extend(values)

            previous_range = current_range
            previous_max_speed = current_max_speed

        speeds.extend(last[1] for t in range(last[0], 101))

        return tuple(int(val) for val in interp(speeds, [0, 100], [0, 255]))
