import abc
from abc import ABC
from pathlib import Path
from typing import List

from .common import InputDevice, mean
import logging

from .lmsensorsdevice import LMSensorsInput, try_and_find_label_for_input

log = logging.getLogger(__name__)


def from_disk_by_id(disk_name: str, sensor_name: str = None):
    disk_lookup_base = Path('/dev/disk/by-id/')
    devices = []

    for device_path in disk_lookup_base.iterdir():
        device = None
        if device_path.name.endswith(disk_name):
            log.debug('exact device match: %s, matches: %s', device_path, disk_name)
            device = create_device(device_path, sensor_name)
        elif disk_name in device_path.name:
            log.debug('potential device match: %s, matches: %s', device_path, disk_name)

            guess_path = disk_lookup_base.joinpath('-'.join(device_path.name.split('-')[0:2]))
            if not guess_path.exists():
                continue

            device = create_device(guess_path, sensor_name)

        if device and device not in devices:
            devices.append(device)

    if devices:
        return devices

    raise FileNotFoundError(f'Could not find hwmon device named: "{disk_name}"')


def create_device(path: Path, sensor_name: str = None):
    name = path.name.split('-')
    device_type = name[0]
    found_name = name[1]
    real_path = path.resolve(True)
    device_name = real_path.name

    mapping = {
        'ata':  ATADrive,
        'nvme': NVMeDrive,
    }
    if device_type == 'nvme':
        return mapping[device_type](path, real_path, found_name, device_name, sensor_name)
    else:
        raise ValueError(f'Unsupported device type: "{device_type}"')


def _resolve_sensors_for_device_path(device_path: Path, expected_sensor_name: str):
    for hwmon in device_path.iterdir():
        hwmon_path = hwmon.joinpath('name')
        if hwmon_path.exists() and hwmon_path.read_text('utf-8') == f'{expected_sensor_name}\n':
            for full_sensor_path in hwmon.iterdir():
                if full_sensor_path.name.startswith('temp') and full_sensor_path.name.endswith('input'):
                    yield full_sensor_path


class DriveDevice(InputDevice, ABC):

    def __init__(self, pretty_path: Path, real_path: Path, found_name: str, device_name: str, sensor_name: str = None):
        self.pretty_path = pretty_path
        self.real_path = real_path
        self.found_name = found_name
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
        return str(self.pretty_path)

    def get_temp(self) -> float:
        return mean((s.get_temp() for s in self.sensors))


class ATADrive(DriveDevice):
    def __init__(self, pretty_path: Path, real_path: Path, found_name: str, device_name: str, sensor_name: str = None):
        super().__init__(pretty_path, real_path, found_name, device_name, None)
        self._check_drivetemp()
        if not self.sensors:
            raise ValueError(f'No sensors found for device: "{real_path}"')

    def _check_drivetemp(self):
        device_path = Path(f'/sys/class/block/{self.device_name}/device/hwmon/')
        for sensor_path in _resolve_sensors_for_device_path(device_path, 'drivetemp'):
            self.sensors.append(LMSensorsInput(sensor_path))


class NVMeDrive(DriveDevice):

    def __init__(self, pretty_path: Path, real_path: Path, found_name: str, device_name: str, sensor_name: str = None):
        super().__init__(pretty_path, real_path, found_name, device_name, sensor_name)
        self.sensors: List[LMSensorsInput] = []
        self._populate_sensors()
        if not self.sensors:
            raise ValueError(f'No sensors found for device: "{real_path}"')

    def _populate_sensors(self):
        device_path = Path(f'/sys/class/nvme/{self.device_name[:-2]}/device/hwmon/')
        for sensor_path in _resolve_sensors_for_device_path(device_path, 'nvme'):
            if self.sensor_name:
                if try_and_find_label_for_input(sensor_path) == self.sensor_name:
                    self.sensors.append(LMSensorsInput(sensor_path))
            else:
                self.sensors.append(LMSensorsInput(sensor_path))
