import logging
from typing import List
from configparser import SectionProxy

from .common import InputDevice, OutputDevice, lerp_range
from .temperaturecontroller import TemperatureController
from .lmsensorsdevice import LMSensorsInput, LMSensorsOutput
from .hddtemp import HDDTemp
from .serialoutput import SerialOutput

log = logging.getLogger(__name__)


def determine_inputs(device_config: SectionProxy) -> List[InputDevice]:
    input_devices = []
    if device_config.get('inputType') == 'componentTemp':
        specific_devices = [k.trim() for k in device_config.get('temperatureMonitorDeviceName').split(',')]
        for idx, path in enumerate([k.trim() for k in device_config.get('temperatureMonitor').split(',')]):
            input_devices.extend(LMSensorsInput.from_path(specific_devices[idx], path))
    elif device_config.get('inputType') == 'hddtemp':
        input_devices.append(HDDTemp())
    else:
        raise ValueError('No Input device created, check the configuration!')

    return input_devices


def determine_outputs(device_config: SectionProxy) -> List[OutputDevice]:
    output_devices = []
    if device_config.get('outputType') == 'fanPWM':
        output_devices.extend(LMSensorsOutput.from_path(device_config.get('outputDeviceName'), device_config.get('device'), device_config.get('outputEnabler')))
    elif device_config.get('outputType') == 'serial':
        output_devices.append(SerialOutput(device_config.getint('device')))
    else:
        raise ValueError('No output device created, check the configuration!')

    return output_devices


def create_device(device_name: str, device_config: SectionProxy):
    """
    creates device from config
    """
    log.debug('Assembling device: %s', device_name)

    device = TemperatureController(
            determine_inputs(device_config),
            determine_outputs(device_config),
            interpolate_temps(device_config)
    )

    if not device:
        return None
    else:
        return device


def interpolate_temps(device_data: SectionProxy) -> List[int]:
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

        if current_max_speed < first[1]:
            continue

        values = lerp_range(
                list(range(previous_range, current_range)),  # current temperature steps
                previous_range, current_range,  # previous max temp range, current max temp range
                previous_max_speed, current_max_speed,  # previous max speed, current max speed
        )

        speeds.extend(values)

        previous_range = current_range
        previous_max_speed = current_max_speed

    speeds.extend(float(last[1]) for _ in range(last[0], 101))

    retval = [int(val) for val in lerp_range(speeds, 0, 100, 0, 255)]
    return retval
