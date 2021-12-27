"""
Module containing the FanController class
"""
import os
import time
import sys
import logging
from pathlib import Path
from typing import Dict

from .temperaturecontroller import TemperatureController


class FanController:
    def __init__(self, pid_file: Path, interval: int, devices: Dict[str, TemperatureController]):
        self.pid_file = pid_file
        self.interval = interval
        self.devices = devices
        self.runnable = False

    def create_pid(self):
        """
        Set up the PID and don't run if we don't manage to write the soggy thing!
        """
        pid = str(os.getpid())
        try:
            if self.pid_file.exists():
                raise RuntimeError('PID file exists, bugging out! Check if pyFC is running?')
            try:
                self.pid_file.write_text(''.join([pid, '\n']))
                logging.info('PID: %s', pid)
            except (PermissionError, IOError):
                msg = 'Failed writing PID file {}, for PID: {}'
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
            self.pid_file.unlink(True)
        except (PermissionError, OSError):
            msg = 'Failed deleting pid file, please purge %s manually.'
            logging.exception(msg, self.pid_file)
            sys.exit(msg.format(self.pid_file))

    def start(self):
        """
        The glorious main loop of the program.
        """
        logging.debug(self.devices)

        for device in self.devices.values():
            device.enable()

        while self.runnable:
            try:
                for device in self.devices.values():
                    device.run()
                outputs = set()
                for c in self.devices.values():
                    outputs.update(c.apply_candidates())

                for o in outputs:
                    o.apply()

                time.sleep(self.interval)
            except Exception as e:
                logging.exception('Caught exception, bailing.')
                self.runnable = False

        for device in self.devices.values():
            device.disable()

    def run(self):
        self.runnable = True

        try:
            self.create_pid()
            self.start()
        finally:
            self.remove_pid()
