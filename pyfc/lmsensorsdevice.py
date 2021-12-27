import logging
from pathlib import Path
from typing import List

from .common import InputDevice, OutputDevice, lerp, ValueBuffer

log = logging.getLogger(__name__)


def try_and_find_label_for_input(path: Path):
    label_path = path.parent.joinpath(path.name.replace('_input', '_label'))
    
    return label_path.read_text('utf-8').replace('\n', '') if label_path.exists() else path.name


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
            with open(potential_device_path, 'r') as potential_file:
                matches = potential_file.read().startswith(device_name)
            log.debug('in dir %s, potential device path: %s, matches: %s', device_dir, potential_device_path, matches)

            if matches:
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
        return [cls(path.joinpath(device_name)) for path in cls.path_from_device_name(sensor_name)]

    def __init__(self, sensor_path: Path):
        """
        :param sensor_path: path to lm-sensors file
        """
        self.path = sensor_path
        self.name = try_and_find_label_for_input(sensor_path)
        self.temp = ValueBuffer(self.name, 35)

    def get_temp(self) -> float:
        try:
            with open(self.path, 'r') as reader:
                value = reader.read()
                floatable = '{}.{}'.format(value[:-4], value[-4:])
                self.temp.update(float(floatable))
        except IOError:
            log.error('Could not read file: {}', self.path)
        try:
            return self.temp.mean()
        except ZeroDivisionError:
            return 35.0

    def __repr__(self):
        return self.name


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
        super().__init__()
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

    def apply(self):
        if not self.enabled:
            return

        speed = round(self.speeds.mean())
        try:
            log.debug('Speed for device: %s set to %s', self.output_file, int(lerp(speed, 0, 255, 0, 100)))
            with open(self.output_file, 'a') as writer:
                writer.write(str(speed))
        except (IOError, PermissionError):
            log.exception('Error writing speed to device: %s', self.output_file)

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
