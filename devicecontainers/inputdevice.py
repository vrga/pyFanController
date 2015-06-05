from abc import ABCMeta, abstractmethod


class InputDevice(metaclass=ABCMeta):
    """
    Abstract class for input devices.
    """
    @abstractmethod
    def get_temp(self):
        pass
