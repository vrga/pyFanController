from pyfc.hddtemp import HDDTemp

"""
/dev/sda|2E256-TL2-500B00|41|C
/dev/sdb|2E256-TL2-500B00|41|C
/dev/sdc|2E256-TL2-500B00|46|C
/dev/sdd|2E256-TL2-500B00|46|C
/dev/sde|CT1000MX500SSD1|30|C
/dev/sdg|CT1000MX500SSD1|27|C
/dev/sdh|CT1000MX500SSD1|30|C
/dev/sdi|CT1000MX500SSD1|30|C
/dev/sdj|ST8000VN004-2M2101|39|C
/dev/sdk|WDC WD8003FFBX-68B9AN0|43|C
"""

temp_f80 = HDDTemp('192.168.3.16', devices=('2E256-TL2-500B00',))
temp_microns = HDDTemp('192.168.3.16', devices=('CT1000MX500SSD1',))
temp_rust = HDDTemp('192.168.3.16', devices=('ST8000VN004-2M2101', 'WDC WD8003FFBX-68B9AN0',))

readings = {}
for _ in range(10):
    for t in (temp_f80, temp_microns, temp_rust):
        devs = tuple(t.devices)
        if devs not in readings:
            readings[devs] = []

        readings[devs].append(t.get_value())

for dev, reading in readings.items():
    print(dev)
    print(reading)
