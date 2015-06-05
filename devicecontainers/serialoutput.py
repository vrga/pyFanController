import logging

import serial
from serial.tools import list_ports

from .outputdevice import OutputDevice


class SerialOutput(OutputDevice):
    """
    Class for communicating with my Atmega 8-16 based PWM fan controller,
    Serial, 9600 baud.
    """

    def __init__(self, device_number):
        self.serial = serial.Serial()
        self.serial.baudrate = 9600
        self.serial_available = False
        self.device_number = device_number

        try:
            """
            Check ttyUSB devices 0 through 9, and get the first one present.
            TODO: stuff this into the config file. Its a stupid way.
            """
            self.serial.port = next(list_ports.grep('ttyUSB[0-9]'))[0]
        except serial.SerialException:
            self.serial_available = False

    def set_speed(self, speed):
        """
        Open serial interface, convert to byte, write data, close serial interface.
        Pray to satan nothing blows up.
        :param speed: speed to set
        :type speed: int
        """
        if self.serial_available:
            try:
                self.serial.open()
                self.serial.write(
                    bytes(
                        ''.join([str(self.device_number), '/', str(speed), '/']),
                        'utf-8'
                    )
                )

                self.serial.close()
                logging.debug(
                    'Speed: %s%% written to device %s on port: %s',
                    str(speed),
                    self.device_number,
                    self.serial.port
                )
            except serial.SerialException:
                self.serial_available = False
        else:
            logging.debug('Written speed would be: %s', str(speed))

    def enable(self):
        """
        attempt to open a serial interface.
        """
        try:
            self.serial.open()
            self.serial_available = True
            self.serial.close()
            logging.debug('Enabled serial communication on port: %s', self.serial.port)
        except serial.SerialException:
            self.serial_available = False
            logging.exception('Failed enabling serial port: %s', self.serial.port)

    def disable(self):
        """
        Attempt to close the serial interface
        """
        try:
            self.serial.close()
            self.serial_available = False
            logging.debug('Disabled serial port: %s', self.serial.port)
        except serial.SerialException:
            self.serial_available = False
            logging.exception('Failed disabling serial port: %s', self.serial.port)

    def __del__(self):
        self.disable()
