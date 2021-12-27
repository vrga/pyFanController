from collections import deque
import time
from pyfc.lmsensorsdevice import LMSensorsInput

from pyfc.drivedevice import from_disk_by_id

sensors = []
sensors.extend(from_disk_by_id('Samsung_SSD_980_PRO_1TB_S5GXNX0R813045N'))
sensors.extend(from_disk_by_id('Samsung_SSD_980_PRO_1TB', 'Composite'))
sensors = set(sensors)
readings = {}
for _ in range(15):
    for t in sensors:
        devs = t.device_name
        if devs not in readings:
            readings[devs] = deque(maxlen=32)

        readings[devs].append(round(t.get_temp(), 2))
    # time.sleep(1)

for dev, reading in readings.items():
    print(dev)
    print(list(reading))
