import logging
from serial import Serial, SerialException
from serial.tools import list_ports

from .common import OutputDevice, mean

log = logging.getLogger(__name__)


class SerialOutput(OutputDevice):
    """
    Class for communicating with my Atmega 8-16 based PWM fan controller,
    Serial, 9600 baud.
    """

    def __init__(self, device_number: str, serial_baud: int = 9600):
        super().__init__(f'serial-{device_number}')
        self.serial = Serial()
        self.serial.baudrate = serial_baud
        self.serial_available = False
        self.device_number = device_number

        try:
            """
            Check ttyUSB devices 0 through 9, and get the first one present.
            TODO: stuff this into the config file. Its a stupid way.
            """
            self.serial.port = next(list_ports.grep('ttyUSB[0-9]'))[0]
        except SerialException:
            self.serial_available = False

    def apply(self):
        """
        Open serial interface, convert to byte, write data, close serial interface.
        Pray to satan nothing blows up.
        :param speed: speed to set
        :type speed: int
        """
        speed = round(self.values.mean())
        if self.serial_available:
            try:
                self.serial.open()
                self.serial.write(bytes(''.join([str(self.device_number), '/', str(speed), '/']), 'utf-8'))
                self.serial.close()
                log.debug(
                        'Speed for device: {}/{} set to {}',
                        self.serial.port,
                        self.device_number,
                        str(speed)
                )
            except SerialException:
                self.serial_available = False
        else:
            log.debug('Written speed would be: {}', speed)

    def enable(self):
        """
        attempt to open a serial interface.
        """
        try:
            self.serial.open()
            self.serial_available = True
            self.serial.close()
            log.debug('Enabled serial communication on port: {}', self.serial.port)
        except SerialException:
            self.serial_available = False
            log.exception('Failed enabling serial port: {}', self.serial.port)

    def disable(self):
        """
        Attempt to close the serial interface
        """
        try:
            self.serial.close()
            self.serial_available = False
            log.debug('Disabled serial port: {}', self.serial.port)
        except SerialException:
            self.serial_available = False
            log.exception('Failed disabling serial port: {}', self.serial.port)

    def __del__(self):
        self.disable()
