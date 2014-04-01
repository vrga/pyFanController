#!/usr/bin/python3.3

"""
The MIT License (MIT)

Copyright (c) 2014 Fran Viktor Pavelić <fv.pavelic@egzodus.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import time
import sys
import configparser
import device

from numpy import interp

debug = False
extras = dict()

def logMe(*value):
    if debug:
        print(value)
"""
    Basic Fan Control class. The setup magic happens here.
"""
class FanController(object):
    def __init__(self):
        #grab config files, setup PID, basic stuff.
        self.devices = dict()
        self.workDir = '/home/vrga/projects/pyFC/'
        os.chdir(self.workDir)
        self.configFile = './setting.ini'
        self.pidFile = '/var/run/pyFC.pid'
        self.createPid()
        self.readConfig()
        # start the main program loop.
        self.runLoop()

    """
        Set up the PID and dont run if we dont manage to write the soggy thing!
        TODO: do better with exceptions...
    """
    def createPid(self):
        try:
            if os.path.exists(self.pidFile):
                raise RuntimeError('PID file exists, bugging out! Check if pyFC is running?')
            try:
                with open(self.pidFile, 'w') as PID:
                    self.pid = os.getpid()
                    logMe('PID: ', self.pid)
                    PID.write(str(self.pid)+'\n')
            except:
                sys.exit('Failed writing PID file')
        except RuntimeError:
            sys.exit(RuntimeError)

    """
        Kill the PID file... 
        TODO: probably a better exception catch here, but eh.
    """
    def removePid(self):
        try:
            os.remove(self.pidFile)
        except OSError:
            pass

    """
        Basic configuration file parsing.
        Thank the heavens for the configparser module...
    """
    def readConfig(self):
        config = configparser.ConfigParser()

        config.read(self.configFile)
        self.setupBase(config['base'])

        logMe(config.sections())
        """
            Here we set up devices, if their config section is actually enabled.
            TODO: check what happens with borked config files...
        """
        # temporarily commented out... probably will stay that way XD
        #for deviceConfig in config.sections():
            #if deviceConfig is not 'base' or config[deviceConfig].getboolean('enabled'):
                #self.devices.update({deviceConfig: device.Device(config[deviceConfig], extras)})
                
        for deviceConfig in config.sections():
            if deviceConfig == 'base' or config[deviceConfig].getboolean('enabled') == False:
                pass
            else:
                self.devices.update({ deviceConfig: device.Device(config[deviceConfig],extras)} )
    """
        continued setup
    """
    def setupBase(self, data):
        """
            If debugging we do not run the loop.
        """
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
            extras.update({'hddtemp' :tmp})
        """
            Conditional import of the module i've devised
            to work with my homebrew Atmega 8 - 16 based PWM fan controller.
            Simple stupid serial communication.
        """
        if data.getboolean('serial'):
            global extras
            import serialFC
            tmp = serialFC.SerialFC()
            extras.update({'serial': tmp})
        """
            Set the running interval for the loop,
            Fall back to 5 seconds, if its not set in the config.
        """
        if data.getint('interval'):
            self.interval = data.getint('interval')
        else:
            self.interval = 5

    """
        Run the program once to see if it will actually even work...
        TODO: rewrite the runOnce and runLoop to restore values they
              originally found when exiting.
    """
    def runOnce(self):
        logMe(self.devices)
        for key in self.devices:
            logMe(key, self.devices[key])
            self.devices[key].getTemps()
            self.devices[key].setTemps()

    """
        The glorious main loop of the program.
        potential TODO: dont write the same thing twice?
    """
    def runLoop(self):
        logMe(self.devices)
        while self.runnable:
            for key in self.devices:
                self.devices[key].getTemps()
                self.devices[key].setTemps()
            time.sleep(self.interval)
    """
        Remove the PID file when we exit.
    """
    def __del__(self):
        self.removePid()

"""
    Run the soggy thing!
    Probably a better way to do this, but eh.
"""
FanController()