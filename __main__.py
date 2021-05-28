"""Executed when package directory is called as a script"""
import configparser
import os
import logging

from pyfc.fancontroller import FanController
from pyfc.deviceloader import create_device
from pathlib import Path


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
    config = configparser.ConfigParser()
    config.read(config_path)

    logging.basicConfig(filename=config['log']['path'], level=config['log']['level'])

    device_identifiers = config['base']['devices'].split(', ')
    device_configuration = {identifier: config[identifier] for identifier in device_identifiers}
    devices = {name: create_device(name, config) for name, config in device_configuration.items()}
    fan_control = FanController(
            Path(config['base']['pid_file']).absolute(),
            config['base'].getint('interval', 5),
            devices
    )
    fan_control.start()


if __name__ == '__main__':
    main()
