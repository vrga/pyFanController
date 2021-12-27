import re
from abc import ABC
from pathlib import Path
from typing import List

from .common import InputDevice, mean, NoSensorsFoundException
import logging

from .lmsensorsdevice import LMSensorsTempInput, try_and_find_label_for_input

log = logging.getLogger(__name__)


class UnsupportedDeviceTypeException(ValueError):
    pass


def from_disk_by_id(disk_name: str, sensor_name: str = None):
    disk_lookup_base = Path('/dev/disk/by-id/')
    device_lookup_regex = r'^(.*?)-(.*?)(-part\d+)?$'
    devices = []
    mapping = {
        'ata':  ATADrive,
        'nvme': NVMeDrive,
    }

    for device_path in disk_lookup_base.iterdir():
        matches = re.match(device_lookup_regex, device_path.name)
        device_type = matches.group(1)
        device_name = matches.group(2)
        if device_type not in mapping:
            continue
        if disk_name not in device_name:
            continue

        if matches.group(3) is not None:
            log.debug('skipping due to having hit partition on device: %s', device_path)
            continue

        device = mapping[device_type](device_path, device_name, sensor_name)

        if device and device not in devices:
            devices.append(device)

    return devices


class DriveDevice(InputDevice, ABC):

    def __init__(self, device_path: Path, device_name: str, sensor_name: str = None):

        super().__init__(device_name)
        self.device_path = device_path
        self.real_path = device_path.resolve()

        self.device_name = device_name
        self.sensor_name = sensor_name

        self.sensors: List[InputDevice] = []

    def __eq__(self, other):
        if not isinstance(other, DriveDevice):
            return False
        return str(self.real_path) == str(other.real_path)

    def __hash__(self):
        return hash(str(self.real_path))

    def __repr__(self):
        return str(self.device_path)

    def get_value(self) -> float:
        return mean((s.get_value() for s in self.sensors))

    def _validate(self):
        if not self.sensors:
            raise NoSensorsFoundException(f'No sensors found for device: "{self.real_path}"')

    def _match_sensor_path(self, path: Path):
        sensor = LMSensorsTempInput(path)
        if self.sensor_name and sensor.name == self.sensor_name:
            yield sensor
        else:
            yield sensor


_hwmon_paths = {}


def _match_hwmon_by_device(match_path: Path):
    if not _hwmon_paths:
        hwmon_path = Path(f'/sys/class/hwmon/')
        for hwmon_dir in hwmon_path.iterdir():
            _hwmon_paths[hwmon_dir.joinpath('device').resolve(True)] = hwmon_dir

    for path, hwmon_dir in _hwmon_paths.items():
        potential_match = set(match_path.parts).symmetric_difference(path.parts)
        if len(potential_match) < 3:
            return hwmon_dir

    raise ValueError('No match found for device "%s"', match_path)


def _handle_hwmon_dir(hwmon_path: Path, hwmon_device_name: str):
    sensor_paths = []
    sensor_name_path = hwmon_path.joinpath('name')
    if sensor_name_path.exists() and sensor_name_path.read_text('utf-8') == f'{hwmon_device_name}\n':
        for full_sensor_path in hwmon_path.iterdir():
            if full_sensor_path.name.startswith('temp') and full_sensor_path.name.endswith('input'):
                log.debug('Matched path: %s', full_sensor_path)
                sensor_paths.append(full_sensor_path)
    return sensor_paths


def find_hwmon_directly(device_path: Path, hwmon_device_name: str):
    sensor_paths = []
    for device_directory in device_path.iterdir():
        # if <device_path>/hwmon*/name == <sensor_name> then return list of <device_path>/hwmon*/temp*_input
        if device_directory.name.startswith('hwmon') and device_directory.name != 'hwmon':
            sensor_paths.extend(_handle_hwmon_dir(device_directory, hwmon_device_name))
        # if <device_path>/hwmon/hwmon*/name == <sensor_name> then return list of <device_path>/hwmon*/temp*_input
        elif device_directory.name == 'hwmon':
            for hwmon_subdir in device_directory.iterdir():
                if hwmon_subdir.name.startswith('hwmon'):
                    sensor_paths.extend(_handle_hwmon_dir(hwmon_subdir, hwmon_device_name))

    return sensor_paths


def find_hwmon_from_device(device_path: Path, hwmon_device_name: str):
    true_path = device_path.resolve()
    hwmon_path = _match_hwmon_by_device(true_path)
    return _handle_hwmon_dir(hwmon_path, hwmon_device_name)


class ATADrive(DriveDevice):
    def __init__(self, device_path: Path, device_name: str, sensor_name: str = None):
        super().__init__(device_path, device_name, None)
        self.find_hwmon_sensors()
        self._validate()

    def find_hwmon_sensors(self):
        device_path = Path(f'/sys/class/block/{self.real_path.name}')

        for sensor_path in find_hwmon_directly(device_path, 'drivetemp'):
            self.sensors.extend(self._match_sensor_path(sensor_path))

        if not self.sensors:
            for sensor_path in find_hwmon_from_device(device_path, 'drivetemp'):
                self.sensors.extend(self._match_sensor_path(sensor_path))


class NVMeDrive(DriveDevice):

    def __init__(self, device_path: Path, device_name: str, sensor_name: str = None):
        super().__init__(device_path, device_name, sensor_name)
        self.sensors: List[LMSensorsTempInput] = []
        self.find_hwmon_sensors()
        self._validate()

    def find_hwmon_sensors(self):
        # from nvme0n1 and similar to just nvme0
        nvme_path = Path(f'/sys/class/nvme/{self.real_path.name[:-2]}')

        def _match_sensor_path(path: Path):
            sensor = LMSensorsTempInput(path)
            if self.sensor_name and sensor.name == self.sensor_name:
                yield sensor
            else:
                yield sensor

        for sensor_path in find_hwmon_directly(nvme_path, 'nvme'):
            self.sensors.extend(_match_sensor_path(sensor_path))

        if not self.sensors:
            for sensor_path in find_hwmon_from_device(nvme_path, 'nvme'):
                self.sensors.extend(_match_sensor_path(sensor_path))
