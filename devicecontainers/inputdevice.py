from abc import ABCMeta, abstractmethod


class InputDevice(metaclass=ABCMeta):
    @abstractmethod
    def get_temp(self):
        pass
