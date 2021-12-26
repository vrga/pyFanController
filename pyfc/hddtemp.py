import logging
import socket
from datetime import datetime, timezone, timedelta
from collections import deque
from typing import Dict

from .common import InputDevice, mean

log = logging.getLogger(__name__)


class TemperaturesBuffer:
    def __init__(self, name):
        self.name = name
        self._buffer = deque(maxlen=32)

    def update(self, value: float):
        self._buffer.append(mean((value, self.mean())))

    def mean(self) -> float:
        try:
            return mean(self._buffer)
        except ZeroDivisionError:
            return 35.0


class TempGroup:
    def __init__(self, name):
        self.name = name
        self._data: Dict[str, TemperaturesBuffer] = {}

    def update(self, name, device):
        if name not in self._data:
            self._data[name] = TemperaturesBuffer(name)

        self._data[name].update(device)

    def mean(self, device) -> float:
        try:
            if device is None:
                return mean(buffer.mean() for buffer in self._data.values())
            return self._data[device].mean()
        except (KeyError, ZeroDivisionError):
            return 35.0


class HDDTemp(InputDevice):
    temps: Dict[str, TempGroup] = {}
    last_read: datetime = datetime.fromtimestamp(-10, timezone.utc)

    """
    Class to access hddtemp data, through the daemon hddtemp uses.
    Requires that you actually run the hddtemp daemon
    on the localhost with the default port.
    """

    def __init__(self, host='127.0.0.1', port=7634, devices=None, time_read_sec=1):
        self.devices = devices if devices else [None]

        self.host = host
        self.port = port

        if self.group_name not in self.temps:
            self.temps[self.group_name] = TempGroup(self.group_name)

        self.time_read = timedelta(seconds=time_read_sec)
        self.available = False

    @property
    def group_name(self):
        return f'{self.host}_{self.port}'

    def get_mean_temp(self) -> float:
        try:
            return mean((self.temps[self.group_name].mean(device) for device in self.devices))
        except ZeroDivisionError:
            return 35.0

    def get_temp(self):
        """
        Get and parse HDD temperatures.
        Works for whatever number of HDD's you might have.
        If the daemon itself returns proper data that is.
        If data cannot be read, assume the temperature is around 35°C.
        """
        now = datetime.now(timezone.utc)
        if now - self.last_read > self.time_read:
            self.read_data()
            self.last_read = now

        return round(self.get_mean_temp(), None)

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

    def read_data(self):
        data = self.try_read()

        hddtemp_string = data.decode('utf-8')

        for temp in hddtemp_string.split('||'):
            try:
                if temp[0] == '|':
                    temp = temp[1:]

                splitted = temp.split('|')
                device_name = splitted[1]
                temperature = float(temp.split('|')[2])
                self.temps[self.group_name].update(device_name, temperature)
            except (IndexError, ValueError):
                continue
            except:
                """
                TODO: figure out what exception can the above actually throw... partially did...
                """
                log.exception('something broke.')
                continue

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
