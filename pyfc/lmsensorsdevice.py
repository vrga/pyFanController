import logging
from pathlib import Path
from typing import List

from .common import InputDevice, OutputDevice, lerp

log = logging.getLogger(__name__)


class LMSensorsDevice:
    @classmethod
    def from_path(cls):
        """
        Implement with constructor of implementing class.
        """
        raise NotImplementedError

    @classmethod
    def path_from_device_name(cls, device_name: str) -> List[Path]:
        device_path = Path('/sys/class/hwmon/')
        matching_paths = []
        for device_dir in device_path.iterdir():
            potential_device_path = device_dir.joinpath('name')
            if potential_device_path.name == device_name:
                matching_paths.append(device_dir)

        if matching_paths:
            return matching_paths

        raise FileNotFoundError(f'Could not find hwmon device named: "{device_name}"')


class LMSensorsInput(InputDevice, LMSensorsDevice):
    """
    Class to handle access to temperatures from lm-sensors
    Because the py3sensors thing is a bit clunky...
    [Note from 2021] Nothing still changed with support for lm-sensors...
    Check https://github.com/torvalds/linux/blob/master/Documentation/hwmon/sysfs-interface.rst for details.
    """

    @classmethod
    def from_path(cls, sensor_name: str, device_name: str) -> List['LMSensorsInput']:
        return [cls(path, device_name) for path in cls.path_from_device_name(sensor_name)]

    def __init__(self, sensor_path: Path, device_name: str):
        """
        :param sensor_path: path to lm-sensors file
        """
        self.path = sensor_path.joinpath(device_name)

    def get_temp(self) -> float:
        try:
            with open(self.path, 'r') as reader:
                temp = reader.read()[:-4]
        except IOError:
            temp = 0
            log.error('Could not read file: {}', self.path)

        return float(temp)


class LMSensorsOutput(OutputDevice, LMSensorsDevice):
    """
    Class to manipulate lm sensors PWM inputs or any other if you so desire.
    [Note from 2021] Nothing still changed with support for lm-sensors...
    Check https://github.com/torvalds/linux/blob/master/Documentation/hwmon/sysfs-interface.rst for details.
    """

    @classmethod
    def from_path(cls, sensor_name: str, device_name: str, enable_file: str) -> List['LMSensorsOutput']:
        return [cls(path, device_name, enable_file) for path in cls.path_from_device_name(sensor_name)]

    def __init__(self, sensor_path: Path, device_name: str, enable_file: str):
        self.output_file = sensor_path.joinpath(device_name)
        self.enable_file = sensor_path.joinpath(enable_file)
        self.old_value = '2'  # default to '2' as old value, this means "automatic fan speed control enabled"
        self.enabled = False

    def get_old_value(self):
        """
        gets and stores the old value of the enabler file,
        so we can at least attempt to be nice about this.
        """
        try:
            with open(self.enable_file, 'r') as reader:
                self.old_value = str(reader.read(1))
        except (IOError, PermissionError):
            self.old_value = '2'
            log.exception('Could not read from enabler file: %s', self.enable_file)

    def enable(self):
        """
        writes '1' to the enabler file.
        """
        self.get_old_value()
        log.debug('writing to enabler: %s', self.enable_file)
        try:
            with open(self.enable_file, 'w') as writer:
                writer.write('1')
            self.enabled = True
        except (IOError, PermissionError):
            log.exception('Error writing to enabling file: %s', self.enable_file)
            self.enabled = False

    def set_speed(self, speed: float):
        if not self.enabled:
            return False

        try:
            log.debug('Speed for device: %s set to %s', self.output_file, int(lerp(speed, 0, 255, 0, 100)))
            with open(self.output_file, 'a') as writer:
                writer.write(str(speed))
                return True
        except (IOError, PermissionError):
            log.exception('Error writing speed to device: %s', self.output_file)
            return False

    def disable(self):
        """
        disable the device.
        """
        try:
            with open(self.enable_file, 'w') as writer:
                writer.write(self.old_value)
        except (IOError, PermissionError):
            log.exception('Error writing to enabling file: %s', self.enable_file)
        finally:
            self.enabled = False

    def __del__(self):
        """
        Always disable when exiting!
        """
        self.disable()