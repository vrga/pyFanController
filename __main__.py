"""Executed when package directory is called as a script"""

import os
import logging

from controllers.fancontroller import FanController
from loaders.configloader import ConfigLoader
from loaders.deviceloader import DeviceLoader


def main():
    """
    ENV constants
    PYFC_CONFIG_PATH
    PYFC_WORK_DIR

    Basic runtime assembly, get paths, either default or from ENV,
    assemble it all and run.
    """
    work_dir = os.environ.get('PYFC_WORK_DIR', os.path.dirname(os.path.abspath(__file__)))
    config_path = os.environ.get('PYFC_CONFIG_PATH', ''.join([work_dir, '/settings.ini']))
    config = ConfigLoader(config_path)

    log_config = config.get('log')
    logging.basicConfig(filename=log_config['path'], level=log_config['level'])

    devices = DeviceLoader(config).create_devices()
    fan_control = FanController(config.get('base'), devices)
    fan_control.runnable = True
    fan_control.run()


if __name__ == '__main__':
    main()
