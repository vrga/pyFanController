from typing import Dict

from .common import mean, ValueBuffer

from datetime import datetime, timezone, timedelta


class TemperatureGroup:
    def __init__(self, name, time_read_sec=1):
        self.name = name
        self.data: Dict[str, ValueBuffer] = {}
        self.last_update = datetime.now(tz=timezone.utc) - timedelta(seconds=10)
        self.time_read = timedelta(seconds=time_read_sec)

    def updatable(self):
        if datetime.now(timezone.utc) - self.last_update > self.time_read:
            return True

        return False

    def update(self, name, device):
        if name not in self.data:
            self.data[name] = ValueBuffer(name, 35)

        self.data[name].update(device)
        self.last_update = datetime.now(timezone.utc)

    def mean(self, device) -> float:
        try:
            if device is None:
                return mean(buffer.mean() for buffer in self.data.values())
            return self.data[device].mean()
        except (KeyError, ZeroDivisionError):
            return 35.0
