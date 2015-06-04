import logging

from .inputdevice import InputDevice


class LMSensorsInputFile(InputDevice):
    """
    Class to handle access to temperatures from lm-sensors
    Because the py3sensors thing is a bit clunky...
    Check http://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/plain/Documentation/hwmon/sysfs-interface?id=HEAD
    for details.
    """

    def __init__(self, file_path):
        """
        :param file_path: path to lm-sensors file
        :type file_path: str
        """
        self.path = file_path

    def get_temp(self):
        try:
            with open(self.path, 'r') as Reader:
                temp = int(Reader.read()[:-4])
        except IOError:
            temp = 0
            logging.error('Could not read file: %s', self.path)

        return temp