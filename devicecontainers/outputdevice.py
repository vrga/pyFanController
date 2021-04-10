from abc import ABCMeta, abstractmethod


class OutputDevice(metaclass=ABCMeta):
    """
    Abstract class for output devices.
    """
    @abstractmethod
    def set_speed(self, speed):
        raise NotImplementedError

    @abstractmethod
    def enable(self):
        raise NotImplementedError

    @abstractmethod
    def disable(self):
        raise NotImplementedError
