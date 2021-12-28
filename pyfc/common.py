import logging
from abc import ABCMeta, abstractmethod
from collections import deque
from typing import List, Union, Iterable, Sequence

log = logging.getLogger(__name__)


class NoSensorsFoundException(RuntimeError):
    pass


class Controller(metaclass=ABCMeta):
    @abstractmethod
    def run(self):
        raise NotImplementedError

    @abstractmethod
    def enable(self):
        raise NotImplementedError

    @abstractmethod
    def disable(self):
        raise NotImplementedError

    @abstractmethod
    def valid(self) -> bool:
        raise NotImplementedError


class InputDevice(metaclass=ABCMeta):
    """
    Abstract class for input devices.
    """

    def __init__(self, name):
        self.name = name
        self.values = ValueBuffer(name, 128)

    @abstractmethod
    def get_value(self) -> float:
        raise NotImplementedError


class OutputDevice(metaclass=ABCMeta):
    """
    Abstract class for output devices.
    """

    def __init__(self, name):
        self.name = name
        self.values = ValueBuffer(name, 128)

    def set_value(self, value: Union[int, float]):
        self.values.update(value)

    @abstractmethod
    def apply(self):
        raise NotImplementedError

    @abstractmethod
    def enable(self):
        raise NotImplementedError

    @abstractmethod
    def disable(self):
        raise NotImplementedError


class PassthroughController(Controller):

    def __init__(self, inputs=Sequence[InputDevice], outputs=Sequence[OutputDevice], speeds=None):
        self.inputs = list(inputs)
        self.outputs = list(outputs)

    def run(self):
        for idx, input_reader in enumerate(self.inputs):
            output = self.outputs[idx]
            output.name = input_reader.name
            output.values.name = input_reader.name
            output.set_value(input_reader.get_value())
            output.apply()
        log.debug('ran loop')

    def apply_candidates(self):
        return self.outputs

    def enable(self):
        for output_dev in self.outputs:
            output_dev.enable()

    def disable(self):
        for output_dev in self.outputs:
            output_dev.disable()

    def valid(self) -> bool:
        return bool(self.inputs and self.outputs) and len(self.inputs) == len(self.outputs)


class DummyInput(InputDevice):
    def __init__(self):
        super().__init__('dummy')
        self.temp = 0

    def get_value(self):
        return self.temp

    def set_value(self, value):
        self.temp = value


class DummyOutput(OutputDevice):
    def __init__(self):
        super().__init__('dummy')
        self.speed = None
        self.enabled = False

    def apply(self):
        if self.enabled:
            self.speed = round(self.values.mean())

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
    if len(seq) == 0:
        raise ValueError('sequence must have at least one value.')
    return sum(seq) / len(seq)


def lerp(value: Union[float, int], input_min: Union[float, int], input_max: Union[float, int], output_min: Union[float, int], output_max: Union[float, int]) -> float:
    if value <= input_min:
        return float(output_min)

    if value >= input_max:
        return float(output_max)

    return (output_min * (input_max - value) + output_max * (value - input_min)) / (input_max - input_min)


def lerp_range(seq: Iterable[Union[float, int]], input_min, input_max, output_min, output_max) -> List[float]:
    return [lerp(val, input_min, input_max, output_min, output_max) for val in seq]


class ValueBuffer:
    def __init__(self, name, default_value=0.0):
        self.name = name
        self.buffer = deque(maxlen=32)
        self._default_value = default_value

    def update(self, value: float):
        self.buffer.append(value)

    def mean(self) -> float:
        try:
            return mean(self.buffer)
        except (ValueError, ZeroDivisionError):
            return self._default_value
