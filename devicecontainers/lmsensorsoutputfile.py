import logging

from .outputdevice import OutputDevice


class LMSensorsOutputFile(OutputDevice):
    """
    Class to manipulate lm sensors PWM inputs or any other if you so desire.
    Check http://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/plain/Documentation/hwmon/sysfs-interface?id=HEAD
    for details.
    """

    def __init__(self, output_file, enable_file):
        self.output_file = output_file
        self.enable_file = enable_file
        self.old_value = '2'
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
            logging.exception('Could not read from enabler file: %s', self.enable_file)

    def enable(self):
        """
        writes '1' to the enabler file.
        """
        self.get_old_value()
        try:
            with open(self.enable_file, 'w') as writer:
                writer.write('1')
            self.enabled = True
        except (IOError, PermissionError):
            logging.exception('Error writing to enabling file: %s', self.enable_file)
            self.enabled = False

    def set_speed(self, speed):
        """
        :param speed: speed to write to set the output to.
        :type speed: int
        """
        if self.enabled:
            logging.debug('Speed for file: %s set to %s', self.output_file, speed)
            try:
                with open(self.output_file, 'w') as writer:
                    writer.write(str(speed))
            except (IOError, PermissionError):
                logging.exception('Error writing to speed file: %s', self.output_file)
        else:
            logging.debug('Speed for file: %s set to %s', self.output_file, speed)

    def disable(self):
        """
        disable the device.
        """
        try:
            with open(self.enable_file, 'w') as writer:
                writer.write(self.old_value)
            self.enabled = False
        except (IOError, PermissionError):
            logging.exception('Error writing to enabling file: %s', self.enable_file)
            self.enabled = False

    def __del__(self):
        """
        Always disable when exiting!
        """
        self.disable()
