import logging
from math import ceil

from numpy import mean

from .inputdevice import InputDevice


class LMSensorsInputFile(InputDevice):
    """
    Class to handle access to temperatures from lm-sensors
    Because the py3sensors thing is a bit clunky...
    Check http://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/plain/Documentation/hwmon/sysfs-interface?id=HEAD
    for details.
    """

    def __init__(self, file_paths):
        """
        :param file_paths: path to lm-sensors file
        :type file_paths: tuple or list
        """
        self.paths = file_paths

    def get_temp(self):
        temp = []
        for path in self.paths:
            try:
                with open(path, 'r') as Reader:
                    temp.append(int(Reader.read()[:-4]))
            except IOError:
                temp.append(0)
                logging.error('Could not read file: %s', path)

        if not temp:
            temp = [0]

        return ceil(mean(temp))
