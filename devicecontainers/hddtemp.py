import socket
import logging
from math import ceil

from common import mean

from .inputdevice import InputDevice

log = logging.getLogger(__name__)


class HDDTemp(InputDevice):
    """
    Class to access hddtemp data, through the daemon hddtemp uses.
    Requires that you actually run the hddtemp daemon
    on the localhost with the default port.
    """

    def __init__(self, host='127.0.0.1', port=7634):
        self.host = host
        self.port = port
        self.socket = socket.socket()
        self.available = False
        self.temps = list()

    def get_temp(self):
        """
        Get and parse HDD temperatures.
        Works for whatever number of HDD's you might have.
        If the daemon itself returns proper data that is.
        If data cannot be read, assume the temperature is around 35°C.
        """
        self.open_socket()

        temps = list()  # type: list[float]

        if self.available:
            data = self.try_read()

            try:
                temperature = data.decode('utf-8').split('||')
            except UnicodeDecodeError:
                temperature = []
                log.exception('hddtemp returned utterly invalid data.')
                self.available = False  # Disable reading from this source in the future.

            for temp in temperature:
                try:
                    if temp[0] == '|':
                        temp = temp[1:]
                    temps.append(float(temp.split('|')[2]))
                except (IndexError, ValueError):
                    temps.append(float(35))
                except:
                    """
                    TODO: figure out what exception can the above actually throw... partially did...
                    """
                    log.exception('something broke.')
                    temps.append(35.0)
        else:
            log.warning('hddtemp daemon not availible. Is it running?')

        if not temps:
            temps.append(35.0)

        return ceil(mean(temps))

    def open_socket(self):
        """
            Basic test to determine availibility of the daemon.
            If not availible, log it.
        """
        if self.available:
            return

        try:
            self.socket.connect((self.host, self.port))
            self.available = True
        except socket.error:
            self.available = False
            log.exception('Failed opening socket to local hddtemp')

    def read_socket(self):
        """
        reads 4096 bytes worth of socket info.
        :return:
        :type :return: str
        """
        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))
        return self.socket.recv(4096)

    def try_read(self):
        """
         tries reading twice, if failing second time marks the whole thing as unavailable.
        :return:
        :type :return: bytes
        """
        try:
            data = self.read_socket()
        except socket.error:
            log.debug('Socket connection died, retrying')
            try:
                self.socket.close()
                self.open_socket()
                data = self.read_socket()
            except socket.error:
                data = ''
                self.available = False
                log.exception('Socket definitely dead. Stopping access attempts')

        return data

    def __del__(self):
        """
            make sure the socket is closed!
        """
        try:
            self.socket.close()
        except socket.error:
            log.exception('Failed opening socket to local hddtemp')
