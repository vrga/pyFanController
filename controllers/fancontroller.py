"""
Module containing the FanController class
"""
import os
import time
import sys
import logging


class FanController(object):
    """
    Basic Fan Control class. The setup magic happens here.
    """

    def __init__(self, config, devices):
        """
        does basic config needed.
        :param config: dict of config values
        :param devices:
        :type devices: dict[str, TemperatureController
        """
        self.pid_file = config['pid_file']
        self.interval = config['interval']
        self.devices = devices
        self.pid = self.create_pid()
        self.runnable = False

    def create_pid(self):
        """
        Set up the PID and don't run if we don't manage to write the soggy thing!
        """
        pid = os.getpid()
        try:
            if os.path.exists(self.pid_file):
                raise RuntimeError('PID file exists, bugging out! Check if pyFC is running?')
            try:
                with open(self.pid_file, 'w') as writer:
                    writer.write(str(pid).join('\n'))
                    logging.info('PID: %s', pid)
            except (PermissionError, IOError):
                msg = 'Failed writing PID file %s, for PID: %d'
                logging.error(msg, self.pid_file, pid)
                sys.exit(msg.format(self.pid_file, pid))
        except RuntimeError:
            logging.exception('%s', RuntimeError)
            sys.exit(RuntimeError)

        return pid

    def remove_pid(self):
        """
        Kill the PID file...
        TODO: probably a better exception catch here, but eh.
        """
        try:
            os.remove(self.pid_file)
        except (PermissionError, OSError):
            msg = 'Failed deleting pid file, please purge %s manually.'
            logging.exception(msg, self.pid_file)
            sys.exit(msg.format(self.pid_file))

    def run(self):
        """
        The glorious main loop of the program.
        potential TODO: dont write the same thing twice?
        """
        logging.debug(self.devices)
        while self.runnable:
            for device in self.devices:
                device.run()
            time.sleep(self.interval)

    def __del__(self):
        """
        Remove the PID file when we exit.
        """
        self.remove_pid()
        for device in self.devices:
            device.disable()
