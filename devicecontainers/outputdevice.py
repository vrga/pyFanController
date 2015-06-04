from abc import ABCMeta, abstractmethod


class OutputDevice(metaclass=ABCMeta):
    @abstractmethod
    def set_speed(self):
        pass

    @abstractmethod
    def enable(self):
        pass
