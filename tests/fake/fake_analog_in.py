from typing import Optional, Callable

ANALOG_CHANNELS = {}
ON_VALUE_CALLBACK: Optional[Callable] = None


def set_on_value_callback(callback: Callable):
    global ON_VALUE_CALLBACK
    ON_VALUE_CALLBACK = callback


class RACExitRequest(Exception):
    def __init__(self):
        super().__init__("exit request")


class FakeAnalogIn:
    def __init__(self, mcp, pin):
        self.mcp = mcp
        self.pin = pin
        self._value = 0
        ANALOG_CHANNELS[self.pin] = self

    @property
    def value(self):
        if ON_VALUE_CALLBACK is not None:
            ON_VALUE_CALLBACK()
        return self._value

    def set_value(self, value):
        self._value = value
