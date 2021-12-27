from collections import deque
import time
from pyfc.lmsensorsdevice import LMSensorsTempInput

sensors = []
for dev in ('nvme', 'coretemp', 'pch_cannonlake', 'iwlwifi_1'):
    sensors.extend(LMSensorsTempInput.from_path(dev, 'temp1_input'))

readings = {}
for _ in range(180):
    for t in sensors:
        devs = t.path
        if devs not in readings:
            readings[devs] = deque(maxlen=32)

        readings[devs].append(round(t.get_value(), 2))
    time.sleep(1)

for dev, reading in readings.items():
    print(dev)
    print(list(reading))
