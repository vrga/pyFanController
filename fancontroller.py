#!/usr/bin/python3.3

import os
import time
import sys
import logging

extras = dict()


class FanController(object):
    """
    Basic Fan Control class. The setup magic happens here.
    """

    def __init__(self, config, devices):
        """
        does basic config needed.
        :param config:
        """
        self.config = config
        os.chdir(self.config.work_dir)
        self.pidFile = self.config.pid_file
        self.interval = self.config.interval
        self.devices = devices
        self.pid = self.create_pid()
        self.runnable = False

    def create_pid(self):
        """
        Set up the PID and dont run if we dont manage to write the soggy thing!
        """
        pid = os.getpid()
        try:
            if os.path.exists(self.pidFile):
                raise RuntimeError('PID file exists, bugging out! Check if pyFC is running?')
            try:
                with open(self.pidFile, 'w') as PID:
                    PID.write(str(pid).join('\n'))
                    logging.info('PID: %s', pid)
            except (PermissionError, IOError):
                msg = 'Failed writing PID file %s, for PID: %d'
                logging.error(msg, self.pidFile, pid)
                sys.exit(msg.format(self.pidFile, pid))
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
            os.remove(self.pidFile)
        except (PermissionError, OSError):
            msg = 'Failed deleting pid file, please purge %s manually.'
            logging.exception(msg, self.pidFile)
            sys.exit(msg.format(self.pidFile))

    def run(self):
        """
        The glorious main loop of the program.
        potential TODO: dont write the same thing twice?
        """
        logging.debug(self.devices)
        while self.runnable:
            for key in self.devices:
                self.devices[key].getTemps()
                self.devices[key].setTemps()
            time.sleep(self.interval)

    def __del__(self):
        """
        Remove the PID file when we exit.
        """
        self.remove_pid()
