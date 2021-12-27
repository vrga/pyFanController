import logging
from typing import List
from configparser import SectionProxy

from .common import InputDevice, OutputDevice, lerp_range
from .drivedevice import DriveDevice, from_disk_by_id
from .temperaturecontroller import TemperatureController
from .lmsensorsdevice import LMSensorsInput, LMSensorsOutput
from .hddtemp import HDDTemp
from .serialoutput import SerialOutput

log = logging.getLogger(__name__)


def generate_component_temp(input_config: SectionProxy) -> List[LMSensorsInput]:
    specific_devices = [k.strip() for k in input_config.get('temperatureMonitorDeviceName').split(',')]
    for idx, path in enumerate([k.strip() for k in input_config.get('temperatureMonitor').split(',')]):
        for s in LMSensorsInput.from_path(specific_devices[idx], path):
            yield s


def generate_hddtemp(input_config: SectionProxy) -> List[HDDTemp]:
    specific_devices = input_config.get('hddtempDevices', None)
    if specific_devices is not None:
        specific_devices = specific_devices.split(',')
    yield HDDTemp(
            input_config.get('hddtempHost', 'localhost'),
            int(input_config.get('hddtempPort', '7634')),
            specific_devices
    )


def generate_drive(input_config: SectionProxy) -> List[DriveDevice]:
    specific_devices = input_config.get('diskIDs').split(',')
    target_sensor_names = input_config.get('diskSensors', None)
    devices = []
    for device_id in specific_devices:
        devices.extend(from_disk_by_id(device_id, target_sensor_names.split(',') if target_sensor_names else None))

    return list(set(devices))


def determine_inputs(device_config: SectionProxy) -> List[InputDevice]:
    input_map = {
        'componentTemp': generate_component_temp(device_config),
        'hddtemp':       generate_hddtemp(device_config),
        'driveDevice':   generate_drive(device_config),
    }

    try:
        return input_map[device_config.get('inputType')](device_config)
    except KeyError:
        raise ValueError('No Input device created, check the configuration!')


def determine_outputs(device_config: SectionProxy) -> List[OutputDevice]:
    output_devices = []
    if device_config.get('outputType') == 'fanPWM':
        output_device = device_config.get('outputDeviceName')
        specific_device_outputs = [k.strip() for k in device_config.get('device').split(',')]
        specific_device_output_enablers = [k.strip() for k in device_config.get('outputEnabler').split(',')]

        for idx, path in enumerate(specific_device_outputs):
            output_devices.extend(LMSensorsOutput.from_path(output_device, path, specific_device_output_enablers[idx]))

    elif device_config.get('outputType') == 'serial':
        output_devices.append(SerialOutput(device_config.getint('device')))
    else:
        raise ValueError('No output device created, check the configuration!')

    return list(output_devices)


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
