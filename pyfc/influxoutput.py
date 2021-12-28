import logging
import re
import time
from typing import Dict, Tuple, List

from functools import partial

from requests import Session

from pyfc.common import OutputDevice

log = logging.getLogger(__name__)


class InfluxLineOutput(OutputDevice):
    _linebuffer: Dict[tuple, List[str]] = {}

    def __init__(self, influx_server_url: str, auth_data: Tuple[str, str], measurement_group: str, measurement_name: str, tags: Dict[str, str]):
        super().__init__(measurement_name)

        self.url = influx_server_url
        self.session = Session()
        self.session.auth = auth_data

        str_template = '{measurement_group},{tags} {measurement_name}={measured_value} {timestamp}'
        self.template_func = partial(
                str_template.format,
                measurement_group=measurement_group,
                tags=','.join((f'{k}={v}' for k, v in tags.items())),
        )
        self._id = (self.url, self.session.auth, measurement_group, ((k, v) for k, v in tags), self.name)

    @property
    def linebuffer(self):
        if self._id not in self._linebuffer:
            log.debug('Didnt find linebuffer, creating a new one.', extra={'id': self._id})
            self._linebuffer[self._id] = []

        return self._linebuffer[self._id]

    def _flush(self):
        if self.linebuffer:
            log.debug('flushing line buffer, lines: %d', len(self.linebuffer))
            self.session.post(self.url, data='\n'.join(self.linebuffer))
            self.linebuffer.clear()

    @property
    def measurement_name(self):
        reg = r'\s'
        return re.sub(reg, '_', self.name)

    def apply(self):
        self.linebuffer.append(self.template_func(timestamp=time.time_ns(), measured_value=self.values.mean(), measurement_name=self.measurement_name))
        if len(self.linebuffer) >= 32:
            self._flush()

    def enable(self):
        pass

    def disable(self):
        self._flush()
