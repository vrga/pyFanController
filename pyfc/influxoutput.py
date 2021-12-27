import time
from typing import Dict, Tuple

from functools import partial

from requests import Session

from pyfc.common import OutputDevice, ValueBuffer


class InfluxLineOutput(OutputDevice):

    def __init__(self, influx_server_url: str, auth_data: Tuple[str, str], measurement_group: str, measurement_name: str, tags: Dict[str, str]):
        super().__init__()

        self.url = influx_server_url
        self.session = Session()
        self.session.auth = auth_data

        str_template = '{measurement_group},{tags} {measurement_name}={measured_value} {timestamp}'
        self.template_func = partial(
                str_template.format,
                measurement_group=measurement_group,
                tags=','.join((f'{k}={v}' for k, v in tags.items())),
                measurement_name=measurement_name
        )

    def apply(self):
        line = self.template_func(timestamp=time.time_ns(), measured_value=self.values.mean())
        self.session.post(self.url, data='\n'.join([line]))

    def enable(self):
        pass

    def disable(self):
        pass
