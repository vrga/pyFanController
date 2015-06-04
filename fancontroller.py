#!/usr/bin/python3.3

import os
import time
import sys
import configparser
import device
import logging

extras = dict()

class FanController(object):
    """
    Basic Fan Control class. The setup magic happens here.
    """

    def __init__(self):
        # grab config files, setup PID, basic stuff.
        self.devices = dict()
        self.workDir = '/home/vrga/projects/pyFC/'
        os.chdir(self.workDir)
        self.configFile = './setting.ini'
        self.pidFile = '/var/run/pyFC.pid'
        self.createPid()
        self.readConfig()
        # start the main program loop.
        self.runLoop()

    def createPid(self):
        """
        Set up the PID and dont run if we dont manage to write the soggy thing!
        TODO: do better with exceptions...
        """
        try:
            if os.path.exists(self.pidFile):
                raise RuntimeError('PID file exists, bugging out! Check if pyFC is running?')
            try:
                with open(self.pidFile, 'w') as PID:
                    self.pid = os.getpid()
                    # logMe('PID: ', self.pid)
                    PID.write(str(self.pid) + '\n')
            except:
                sys.exit('Failed writing PID file')
        except RuntimeError:
            sys.exit(RuntimeError)

    def removePid(self):
        """
        Kill the PID file...
        TODO: probably a better exception catch here, but eh.
        """
        try:
            os.remove(self.pidFile)
        except OSError:
            pass

    def readConfig(self):
        """
        Basic configuration file parsing.
        Thank the heavens for the configparser module...
        """
        config = configparser.ConfigParser()

        config.read(self.configFile)
        self.setupBase(config['base'])

        # logMe(config.sections())
        """
            Here we set up devices, if their config section is actually enabled.
            TODO: check what happens with borked config files...
        """
        # temporarily commented out... probably will stay that way XD
        # for deviceConfig in config.sections():
        # if deviceConfig is not 'base' or config[deviceConfig].getboolean('enabled'):
        #     self.devices.update({deviceConfig: device.Device(config[deviceConfig], extras)})

        for deviceConfig in config.sections():
            if deviceConfig == 'base' or config[deviceConfig].getboolean('enabled') == False:
                pass
            else:
                self.devices.update({deviceConfig: device.Device(config[deviceConfig], extras)})

    def setupBase(self, data):
        """
            continued setup
        """

        # If debugging we do not run the loop.

        if data.getboolean('debug'):
            global debug
            debug = data.getboolean('debug')
            self.runnable = False
        else:
            self.runnable = True
        """
            Conditional import of the hddtemp checker.
            Requires that you actually run the hddtemp daemon 
            on the localhost with the default port.
            TODO: maybe generalise this?
        """
        if data.getboolean('hddtemp'):
            global extras
            import hddtempSocket as hddt

            tmp = hddt.hddtemp()
            extras.update({'hddtemp': tmp})
        """
            Conditional import of the module i've devised
            to work with my homebrew Atmega 8 - 16 based PWM fan controller.
            Simple stupid serial communication.
        """
        if data.getboolean('serial'):
            global extras
            import serialfc

            tmp = serialfc.SerialFC()
            extras.update({'serial': tmp})
        """
            Set the running interval for the loop,
            Fall back to 5 seconds, if its not set in the config.
        """
        if data.getint('interval'):
            self.interval = data.getint('interval')
        else:
            self.interval = 5

    def runOnce(self):
        """
        Run the program once to see if it will actually even work...
        TODO: rewrite the runOnce and runLoop to restore values they
              originally found when exiting.
        """
        # logMe(self.devices)
        for key in self.devices:
            # logMe(key, self.devices[key])
            self.devices[key].getTemps()
            self.devices[key].setTemps()

    def runLoop(self):
        """
        The glorious main loop of the program.
        potential TODO: dont write the same thing twice?
        """
        # logMe(self.devices)
        while self.runnable:
            for key in self.devices:
                self.devices[key].getTemps()
                self.devices[key].setTemps()
            time.sleep(self.interval)

    def __del__(self):
        """
        Remove the PID file when we exit.
        """
        self.removePid()


"""
    Run the soggy thing!
    Probably a better way to do this, but eh.
"""
FanController()
