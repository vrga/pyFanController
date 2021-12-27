import logging
from typing import List, Iterable
from configparser import SectionProxy

from .common import InputDevice, OutputDevice, lerp_range
from .drivedevice import DriveDevice, from_disk_by_id
from .influxoutput import InfluxLineOutput
from .temperaturecontroller import TemperatureController
from .lmsensorsdevice import LMSensorsTempInput, LMSensorsOutput
from .hddtemp import HDDTemp
from .serialoutput import SerialOutput

log = logging.getLogger(__name__)


def generate_component_temp_input(input_config: SectionProxy) -> Iterable[LMSensorsTempInput]:
    specific_devices = input_config.getlist('temperatureMonitorDeviceName')
    for idx, path in enumerate(input_config.getlist('temperatureMonitor')):
        for s in LMSensorsTempInput.from_path(specific_devices[idx], path):
            yield s


def generate_hddtemp_input(input_config: SectionProxy) -> Iterable[HDDTemp]:
    specific_devices = input_config.getlist('hddtempDevices', None)
    yield HDDTemp(
            input_config.get('hddtempHost', 'localhost'),
            int(input_config.get('hddtempPort', '7634')),
            specific_devices
    )


def generate_drive_input(input_config: SectionProxy) -> List[DriveDevice]:
    specific_devices = input_config.getlist('diskIDs')
    devices = []
    for device_id in specific_devices:
        devices.extend(from_disk_by_id(device_id, input_config.getlist('diskSensors', None)))

    return list(set(devices))


def determine_inputs(device_config: SectionProxy) -> Iterable[InputDevice]:
    input_map = {
        'componentTemp': generate_component_temp_input,
        'hddtemp':       generate_hddtemp_input,
        'driveDevice':   generate_drive_input,
    }

    try:
        return input_map[device_config.get('inputType')](device_config)
    except (KeyError, FileNotFoundError):
        log.error('Failed creating device!', exc_info=True)
        return []


def generate_pwm_output(device_config: SectionProxy) -> Iterable[LMSensorsOutput]:
    output_device = device_config.get('outputDeviceName')
    specific_device_outputs = device_config.getlist('device')
    specific_device_output_enablers = device_config.getlist('outputEnabler')

    for idx, path in enumerate(specific_device_outputs):
        yield LMSensorsOutput.from_path(output_device, path, specific_device_output_enablers[idx])


def generate_serial_output(device_config: SectionProxy) -> Iterable[SerialOutput]:
    yield SerialOutput(device_config.getint('device'))


def generate_influx_output(device_config: SectionProxy) -> Iterable[InfluxLineOutput]:
    auth = (device_config.get('influxServerUser', None), device_config.get('influxServerPassword', None))
    if not (auth[0] and auth[1]):
        auth = None

    tag_keys = device_config.getlist('influxTagKeys', None)
    tag_values = device_config.getlist('influxTagValues', None)
    if tag_keys and tag_values:
        tags = dict(zip(tag_keys, tag_values))
    else:
        tags = {}

    yield InfluxLineOutput(
            device_config.get('influxServerURL'),
            auth,
            device_config.get('influxGroup'),
            device_config.get('influxMeasurementName'),
            tags
    )


def determine_outputs(device_config: SectionProxy) -> Iterable[OutputDevice]:
    output_map = {
        'fanPWM': generate_pwm_output,
        'serial': generate_serial_output,
        'influx': generate_influx_output,
    }
    try:
        return output_map[device_config.get('outputType')](device_config)
    except (KeyError, FileNotFoundError):
        log.error('Failed creating device!', exc_info=True)
    return []


def create_device(device_name: str, device_config: SectionProxy) -> TemperatureController:
    """
    creates device from config
    """
    log.debug('Assembling device: %s', device_name)

    device = TemperatureController(
            determine_inputs(device_config),
            determine_outputs(device_config),
            interpolate_temps(device_config)
    )

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

    speeds.extend(float(last[1]) for _ in range(last[0], 102))

    return [int(val) for val in lerp_range(speeds, 0, 100, 0, 255)]
