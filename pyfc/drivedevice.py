import re
from abc import ABC
from pathlib import Path
from typing import List

from .common import InputDevice, mean, NoSensorsFoundException
import logging

from .lmsensorsdevice import LMSensorsInput, try_and_find_label_for_input

log = logging.getLogger(__name__)


class UnsupportedDeviceTypeException(ValueError):
    pass


def from_disk_by_id(disk_name: str, sensor_name: str = None):
    disk_lookup_base = Path('/dev/disk/by-id/')
    devices = []

    for device_path in disk_lookup_base.iterdir():
        device = None
        try:
            if device_path.name.endswith(disk_name):
                log.debug('exact device match: %s, matches: %s', device_path, disk_name)
                device = create_device(device_path, sensor_name)
            elif disk_name in device_path.name:
                log.debug('potential device match: %s, matches: %s', device_path, disk_name)
                regex = r'^(.*?)-(.*?)(-part\d+)?$'
                matches = re.match(regex, device_path.name)
                guess_path = disk_lookup_base.joinpath('-'.join(matches.group(1, 2)))
                if not guess_path.exists():
                    log.debug('guessed path incorrect for device: %s', device_path)
                    continue

                if matches.group(3) is not None:
                    log.debug('skipping due to having hit partition on device: %s', device_path)
                    continue

                device = create_device(guess_path, sensor_name)

            if device and device not in devices:
                devices.append(device)
        except UnsupportedDeviceTypeException as e:
            log.warning(e, exc_info=True)
            continue

    if devices:
        return devices

    raise FileNotFoundError(f'Could not find hwmon device named: "{disk_name}"')


def create_device(path: Path, sensor_name: str = None):
    regex = r'^(.*?)-(.*?)(-part\d+)?$'
    matches = re.match(regex, path.name)

    device_type = matches.group(1)
    found_name = matches.group(2)
    real_path = path.resolve()
    device_name = real_path.name

    mapping = {
        'ata':  ATADrive,
        'nvme': NVMeDrive,
    }

    try:
        return mapping[device_type](path, real_path, found_name, device_name, sensor_name)
    except KeyError:
        raise UnsupportedDeviceTypeException(f'Unsupported device type: "{device_type}"')


def _resolve_sensors_for_device_path(device_path: Path, expected_sensor_name: str):
    sensors = []
    for hwmon in device_path.iterdir():
        hwmon_path = hwmon.joinpath('name')
        if hwmon_path.exists() and hwmon_path.read_text('utf-8') == f'{expected_sensor_name}\n':
            sensors.extend(_resolve_direct_sensors_for_hwmon_dir(hwmon))
    return sensors


def _resolve_direct_sensors_for_hwmon_dir(hwmon_dir: Path):
    sensors = []
    for full_sensor_path in hwmon_dir.iterdir():
        if full_sensor_path.name.startswith('temp') and full_sensor_path.name.endswith('input'):
            log.debug('Matched path: %s', full_sensor_path)
            sensors.append(LMSensorsInput(full_sensor_path))

    if not sensors:
        log.debug('Did not match anything under: %s', hwmon_dir)

    return sensors


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

    def _validate(self):
        if not self.sensors:
            raise NoSensorsFoundException(f'No sensors found for device: "{self.real_path}"')


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


class ATADrive(DriveDevice):
    def __init__(self, pretty_path: Path, real_path: Path, found_name: str, device_name: str, sensor_name: str = None):
        super().__init__(pretty_path, real_path, found_name, device_name, None)
        self._check_drivetemp()
        self._validate()

    def _check_drivetemp(self):
        device_path = Path(f'/sys/class/block/{self.device_name}/device')
        hwmon_path = device_path.joinpath('hwmon')
        if hwmon_path.exists():
            for sensor_path in _resolve_sensors_for_device_path(hwmon_path, 'drivetemp'):
                self.sensors.append(LMSensorsInput(sensor_path))
        else:
            true_path = device_path.resolve()
            for sensor_path in _resolve_sensors_for_device_path(_match_hwmon_by_device(true_path), 'drivetemp'):
                self.sensors.append(LMSensorsInput(sensor_path))


class NVMeDrive(DriveDevice):

    def __init__(self, pretty_path: Path, real_path: Path, found_name: str, device_name: str, sensor_name: str = None):
        super().__init__(pretty_path, real_path, found_name, device_name, sensor_name)
        self.sensors: List[LMSensorsInput] = []
        self._populate_sensors()
        self._validate()

    def _populate_sensors(self):
        nvme_path = Path(f'/sys/class/nvme/{self.device_name[:-2]}')

        def _match_sensor_path(path: Path):
            if self.sensor_name:
                if try_and_find_label_for_input(path) == self.sensor_name:
                    yield LMSensorsInput(path)
            else:
                yield LMSensorsInput(path)

        for nvme_dir in nvme_path.iterdir():
            if nvme_dir.name.startswith('hwmon'):
                for sensor_path in _resolve_sensors_for_device_path(nvme_dir, 'nvme'):
                    self.sensors.extend(_match_sensor_path(sensor_path))

        if not self.sensors:
            true_path = nvme_path.joinpath('device').resolve().joinpath(f'nvme/{self.device_name[:-2]}').resolve()
            self.sensors.extend(_resolve_direct_sensors_for_hwmon_dir(_match_hwmon_by_device(true_path)))
