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

import serial
from serial.tools import list_ports

debug = True

def logMe(*value):
    if debug:
        print(value)

"""
    Class for communicating with my Atmega 8-16 based PWM fan controller,
    Serial, 9600 baud.
"""
class SerialFC(object):
    """
        Basic initialisation and availibility check.
    """
    def __init__(self):
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        """
            Check ttyUSB devices 0 through 9, and get the first one present.
            TODO: stuff this into the config file. Its a stupid way.
        """
        try:
            self.ser.port = next(list_ports.grep('ttyUSB[0-9]'))[0]
        except:
            pass
        """
            Test for serial interface availibility.
        """
        try:
            self.ser.open()
            self.serialAvailible = True
            self.ser.close()
        except:
            logMe('Failed opening serial port')
            self.serialAvailible = False
    """
        Open serial interface, write data, close serial interface.
        Pray to satan nothing blows up.
    """
    def write(self, data):
        self.ser.open()
        self.ser.write(data)
        self.ser.close()
