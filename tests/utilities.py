import pygame
import os
import toml
from tests.fake.fake_analog_in import ANALOG_CHANNELS, set_on_value_callback

RISING_CALLBACKS = {}
FALLING_CALLBACKS = {}
PIN_DICT = {}
REVERSE_PIN_DICT = {}
PIN_VALUES = {}
KEY_TO_INPUT_MAP = {
    pygame.K_a: "left_pressure_pad_pin",
    pygame.K_s: "middle_pressure_pad_pin",
    pygame.K_d: "right_pressure_pad_pin",
}


class RACExitRequest(Exception):
    def __init__(self):
        super().__init__("exit request")


def init(configuration_file):
    global PIN_DICT
    global REVERSE_PIN_DICT
    global PIN_VALUES
    pygame.mixer.pre_init(22050, -16, 1, 1024)
    pygame.mixer.init()
    pygame.display.init()
    pygame.display.set_mode((1280, 768))
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), configuration_file)) as fh:
        PIN_DICT = toml.load(fh)
    REVERSE_PIN_DICT = {v: k for k, v in PIN_DICT.items()}
    PIN_VALUES = {k: 0 for k in REVERSE_PIN_DICT}
    print("TEST_MODE: Running in test mode!")
    for k, v in KEY_TO_INPUT_MAP.items():
        print(f"TEST_MODE: Press {pygame.key.name(k)} to activate {v}")
    set_on_value_callback(process_events)


def process_events():
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key in KEY_TO_INPUT_MAP:
                activate_input = KEY_TO_INPUT_MAP[event.key]
                print(f"TEST_MODE: Activating {activate_input}", flush=True)
                pin = PIN_DICT[activate_input]
                if pin in ANALOG_CHANNELS:
                    ANALOG_CHANNELS[pin].set_value(10000)
            elif event.key == pygame.K_ESCAPE:
                raise RACExitRequest()
        elif event.type == pygame.KEYUP:
            if event.key in KEY_TO_INPUT_MAP:
                activate_input = KEY_TO_INPUT_MAP[event.key]
                print(f"TEST_MODE: Deactivating {activate_input}", flush=True)
                pin = PIN_DICT[activate_input]
                if pin in ANALOG_CHANNELS:
                    ANALOG_CHANNELS[pin].set_value(0)
