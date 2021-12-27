"""Executed when package directory is called as a script"""
import configparser
import os
import logging
import sys

from pyfc.fancontroller import FanController
from pyfc.deviceloader import create_device
from pathlib import Path

log = logging.getLogger(__name__)


def main():
    """
    ENV constants
    PYFC_CONFIG_PATH
    PYFC_WORK_DIR

    Basic runtime assembly, get paths, either default or from ENV,
    assemble it all and run.
    """

    work_dir = os.environ.get('PYFC_WORK_DIR', Path(__file__).absolute().parent)
    config_path = os.environ.get('PYFC_CONFIG_PATH', Path(work_dir).joinpath('settings.ini'))
    config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
    config.read(config_path)

    if config['log']['path'] == 'stdout':
        logging.basicConfig(stream=sys.stdout, level=config['log']['level'])
    else:
        logging.basicConfig(filename=config['log']['path'], level=config['log']['level'])

    device_identifiers = config['base']['devices'].split(', ')
    device_configuration = {identifier: config[identifier] for identifier in device_identifiers}
    devices = {name: create_device(name, config) for name, config in device_configuration.items()}

    valid_devices = {}
    for name, device in devices.items():
        if device.valid():
            valid_devices[name] = device
        else:
            log.warning('Configured device is not valid, removing controller. %s', name)

    fan_control = FanController(
            Path(config['base']['pid_file']).absolute(),
            config['base'].getint('interval', 5),
            valid_devices
    )
    fan_control.run()


if __name__ == '__main__':
    main()
