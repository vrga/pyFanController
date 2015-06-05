from abc import ABCMeta, abstractmethod


class OutputDevice(metaclass=ABCMeta):
    """
    Abstract class for output devices.
    """
    @abstractmethod
    def set_speed(self, speed):
        pass

    @abstractmethod
    def enable(self):
        pass

    @abstractmethod
    def disable(self):
        pass
