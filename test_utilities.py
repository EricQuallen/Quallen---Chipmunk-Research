import pygame
import os
import json

# Private constants
_RISING_CALLBACKS = {}
_FALLING_CALLBACKS = {}
_PIN_DICT = {}
_REVERSE_PIN_DICT = {}
_PIN_VALUES = {}
_ANALOG_CHANNELS = {}
_KEY_TO_INPUT_MAP = {
    pygame.K_a: "left_pressure_pad",
    pygame.K_s: "middle_pressure_pad",
    pygame.K_d: "right_pressure_pad",
}


class FakeStepper:
    def __init__(self, address, stepper_id):
        self.address = address
        self.id = stepper_id

    def onestep(self):
        pass


class FakeMotorKit:
    def __init__(self, address):
        self.address = address
        self.stepper1 = FakeStepper(address, 1)
        self.stepper2 = FakeStepper(address, 2)


class FakeAnalogIn:
    def __init__(self, mcp, pin):
        self.mcp = mcp
        self.pin = pin
        self._value = 0
        _ANALOG_CHANNELS[self.pin] = self

    @property
    def value(self):
        process_events()
        return self._value

    def set_value(self, value):
        self._value = value


class RACExitRequest(Exception):
    def __init__(self):
        super().__init__("exit request")


def init():
    global _PIN_DICT
    global _REVERSE_PIN_DICT
    global _PIN_VALUES
    pygame.mixer.pre_init(22050, -16, 1, 1024)
    pygame.mixer.init()
    pygame.display.init()
    pygame.display.set_mode((1280, 768))
    with open(os.path.join(os.path.dirname(__file__), "pin_mapping.json")) as fh:
        _PIN_DICT = json.load(fh)
    _REVERSE_PIN_DICT = {v: k for k, v in _PIN_DICT.items()}
    _PIN_VALUES = {k: 0 for k in _REVERSE_PIN_DICT}
    print("_PIN_VALUES:", _PIN_VALUES)
    print("Running in test mode!.")
    for k, v in _KEY_TO_INPUT_MAP.items():
        print(f"Press {pygame.key.name(k)} to activate {v}")


def process_events():
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key in _KEY_TO_INPUT_MAP:
                activate_input = _KEY_TO_INPUT_MAP[event.key]
                print(f"Activating {activate_input}", flush=True)
                _ANALOG_CHANNELS[_PIN_DICT[activate_input]].set_value(10000)
            elif event.key == pygame.K_ESCAPE:
                raise RACExitRequest()
        elif event.type == pygame.KEYUP:
            if event.key in _KEY_TO_INPUT_MAP:
                activate_input = _KEY_TO_INPUT_MAP[event.key]
                print(f"Deactivating {activate_input}", flush=True)
                _ANALOG_CHANNELS[_PIN_DICT[activate_input]].set_value(0)
