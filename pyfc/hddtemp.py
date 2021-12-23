import itertools
import logging
import socket
from collections import deque
from math import ceil

from .common import InputDevice, mean

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
        self.available = False
        self.temps = {}

    def get_mean_temp(self) -> float:
        if not self.temps:
            return 35.0

        return mean(list(itertools.chain.from_iterable(self.temps.values())))

    def get_temp(self):
        """
        Get and parse HDD temperatures.
        Works for whatever number of HDD's you might have.
        If the daemon itself returns proper data that is.
        If data cannot be read, assume the temperature is around 35°C.
        """

        data = self.try_read()

        hddtemp_string = data.decode('utf-8')

        for temp in hddtemp_string.split('||'):
            try:
                if temp[0] == '|':
                    temp = temp[1:]

                splitted = temp.split('|')
                device = splitted[0]
                device_name = splitted[1]
                temperature = float(temp.split('|')[2])

                if (device, device_name) not in self.temps:
                    self.temps[(device, device_name)] = deque(maxlen=32)

                self.temps[(device, device_name)].append(temperature)
            except (IndexError, ValueError):
                continue
            except:
                """
                TODO: figure out what exception can the above actually throw... partially did...
                """
                log.exception('something broke.')
                continue

        return ceil(self.get_mean_temp())

    def read_socket(self):
        """
        reads 4096 bytes worth of socket info.
        :return:
        :type :return: str
        """
        a_socket = socket.socket()
        a_socket.connect((self.host, self.port))
        data = a_socket.recv(4096)
        a_socket.close()
        return data

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
                data = self.read_socket()
            except socket.error:
                data = ''
                self.available = False
                log.exception('Socket definitely dead. Stopping access attempts')

        return data
