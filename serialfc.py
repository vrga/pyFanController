import serial
from serial.tools import list_ports
import logging

class SerialFC(object):
    """
    Class for communicating with my Atmega 8-16 based PWM fan controller,
    Serial, 9600 baud.
    """

    def __init__(self):
        """
        Basic initialisation and availibility check.
        """
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
            self.serialAvailible = False

    def write(self, data):
        """
        Open serial interface, write data, close serial interface.
        Pray to satan nothing blows up.
        """
        self.ser.open()
        self.ser.write(data)
        self.ser.close()
