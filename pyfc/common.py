from abc import ABCMeta, abstractmethod
from typing import List, Union, Iterable, Sequence


class NoSensorsFoundException(RuntimeError):
    pass


class InputDevice(metaclass=ABCMeta):
    """
    Abstract class for input devices.
    """

    @abstractmethod
    def get_temp(self) -> float:
        raise NotImplementedError


class OutputDevice(metaclass=ABCMeta):
    """
    Abstract class for output devices.
    """

    def __init__(self):
        self.speeds = []

    def set_speed(self, speed: Union[int, float]):
        self.speeds.append(round(speed))

    def apply(self):
        self._apply()
        self.speeds.clear()

    @abstractmethod
    def _apply(self):
        raise NotImplementedError

    @abstractmethod
    def enable(self):
        raise NotImplementedError

    @abstractmethod
    def disable(self):
        raise NotImplementedError


class DummyInput(InputDevice):
    def __init__(self):
        self.temp = 0

    def get_temp(self) -> float:
        return self.temp

    def set_temp(self, value):
        self.temp = value


class DummyOutput(OutputDevice):
    def __init__(self):
        super().__init__()
        self.speed = None
        self.enabled = False

    def _apply(self):
        if self.enabled:
            self.speed = round(mean(self.speeds))

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False


def mean(seq: Iterable) -> float:
    if not isinstance(seq, Iterable):
        raise ValueError('provided sequence MUST be iterable')
    if not isinstance(seq, Sequence):
        seq = list(seq)
    if len(seq) == 1:
        return float(seq[0])
    return sum(seq) / len(seq)


def lerp(value: Union[float, int], input_min: Union[float, int], input_max: Union[float, int], output_min: Union[float, int], output_max: Union[float, int]) -> float:
    if value <= input_min:
        return float(output_min)

    if value >= input_max:
        return float(output_max)

    return (output_min * (input_max - value) + output_max * (value - input_min)) / (input_max - input_min)


def lerp_range(seq: Iterable[Union[float, int]], input_min, input_max, output_min, output_max) -> List[float]:
    return [lerp(val, input_min, input_max, output_min, output_max) for val in seq]
