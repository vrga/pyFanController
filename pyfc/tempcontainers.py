from typing import Dict

from .common import mean

from datetime import datetime, timezone, timedelta
from collections import deque


class TemperaturesBuffer:
    def __init__(self, name):
        self.name = name
        self.buffer = deque(maxlen=32)

    def update(self, value: float):
        self.buffer.append(mean((value, self.mean())))

    def mean(self) -> float:
        try:
            return mean(self.buffer)
        except ZeroDivisionError:
            return 35.0


class TemperatureGroup:
    def __init__(self, name, time_read_sec=1):
        self.name = name
        self.data: Dict[str, TemperaturesBuffer] = {}
        self.last_update = datetime.now(tz=timezone.utc) - timedelta(seconds=10)
        self.time_read = timedelta(seconds=time_read_sec)

    def updatable(self):
        if datetime.now(timezone.utc) - self.last_update > self.time_read:
            return True

        return False

    def update(self, name, device):
        if name not in self.data:
            self.data[name] = TemperaturesBuffer(name)

        self.data[name].update(device)
        self.last_update = datetime.now(timezone.utc)

    def mean(self, device) -> float:
        try:
            if device is None:
                return mean(buffer.mean() for buffer in self.data.values())
            return self.data[device].mean()
        except (KeyError, ZeroDivisionError):
            return 35.0
