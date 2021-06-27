# Phony implementation of GPIO
# import pygame
import os
import json

# Publicly available constants from the GPIO package
BCM = 0
IN = 0
OUT = 0
PUD_UP = 0
FALLING = 0
RISING = 1

# Private constants specifically for the phony GPIO package
# _RISING_CALLBACKS = {}
# _FALLING_CALLBACKS = {}
# _PIN_DICT = {}
# _REVERSE_PIN_DICT = {}
# _PIN_VALUES = {}
# _KEY_TO_INPUT_MAP = {
#     pygame.K_a: "left_pressure_pad",
#     pygame.K_s: "middle_pressure_pad",
#     pygame.K_d: "right_pressure_pad",
# }
#
# responses = []
# wait_time = 0
#
#
# class RACExitRequest(Exception):
#     def __init__(self):
#         super().__init__("exit request")


def setmode(_):
    pass
    # global _PIN_DICT
    # global _REVERSE_PIN_DICT
    # global _PIN_VALUES
    # pygame.mixer.pre_init(22050, -16, 1, 1024)
    # pygame.mixer.init()
    # pygame.display.init()
    # pygame.display.set_mode((1280, 768))
    # with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "pin_mapping.json")) as fh:
    #     _PIN_DICT = json.load(fh)
    # _REVERSE_PIN_DICT = {v: k for k, v in _PIN_DICT.items()}
    # _PIN_VALUES = {k: 0 for k in _REVERSE_PIN_DICT}
    # print("_PIN_VALUES:", _PIN_VALUES)
    # print("Using the RPi phony package.")
    # for k, v in _KEY_TO_INPUT_MAP.items():
    #     print(f"Press {pygame.key.name(k)} to activate {v}")


# noinspection PyUnusedLocal
def setup(index, value, pull_up_down=None):
    pass

        
def output(pin, value):
    print("pin:", pin, value)
    # global wait_time
    # print(f"{_REVERSE_PIN_DICT[pin]}={value}")
    # if pin == _PIN_DICT["left_conveyor_turn_counterclockwise"]:
    #     # Now we have to simulate the conveyor turning
    #     _PIN_VALUES[_PIN_DICT["left_conveyor_sensor"]] = 1
    #     wait_time = 5
    #     responses.append(("left_conveyor_sensor", 0))
    #     pass


# noinspection PyShadowingBuiltins
def input(pin):
    pass


def remove_event_detect(bla):
    pass


def cleanup():
    pass


def add_event_detect(pin, sign, callback=None, bouncetime=None):
    pass

# def handle_callbacks(pin, sign):
#     if sign == FALLING:
#         if pin in _FALLING_CALLBACKS:
#             for callback in _FALLING_CALLBACKS[pin]:
#                 callback(pin)
#     elif sign == RISING:
#         if pin in _RISING_CALLBACKS:
#             for callback in _RISING_CALLBACKS[pin]:
#                 callback(pin)
#
#
# def process_events():
#     for event in pygame.event.get():
#         if event.type == pygame.KEYDOWN:
#             if event.key in _KEY_TO_INPUT_MAP:
#                 activate_input = _KEY_TO_INPUT_MAP[event.key]
#                 print(f"Activating {activate_input}", flush=True)
#                 _PIN_VALUES[_PIN_DICT[activate_input]] = 1
#                 handle_callbacks(_PIN_DICT[activate_input], RISING)
#             elif event.key == pygame.K_ESCAPE:
#                 raise RACExitRequest()
#         elif event.type == pygame.KEYUP:
#             if event.key in _KEY_TO_INPUT_MAP:
#                 activate_input = _KEY_TO_INPUT_MAP[event.key]
#                 print(f"Deactivating {activate_input}", flush=True)
#                 _PIN_VALUES[_PIN_DICT[activate_input]] = 0
#                 handle_callbacks(_PIN_DICT[activate_input], FALLING)
#
#
# def _process_scheduled_events():
#     global wait_time
#     pin_callbacks = []
#     if wait_time > 0:
#         wait_time -= 1
#     else:
#         while len(responses) > 0:
#             response = responses.pop(0)
#             #print("GPIO: Response:", response, flush=True)
#             if isinstance(response, int):
#                 if response == -1:
#                     raise RACExitRequest()
#                 wait_time = response
#                 break
#             elif hasattr(response, "__call__"):
#                 response()
#             else:
#                 pin_name, value = response
#                 if value > _PIN_VALUES[_PIN_DICT[pin_name]]:
#                     sign = RISING
#                 elif value < _PIN_VALUES[_PIN_DICT[pin_name]]:
#                     sign = FALLING
#                 else:
#                     # If the sign is neither rising nor falling, nothing as changed
#                     continue
#
#                 _PIN_VALUES[_PIN_DICT[pin_name]] = value
#                 pin_callbacks.append((_PIN_DICT[pin_name], sign))
#
#     for pin, sign in pin_callbacks:
#         handle_callbacks(pin, sign)



    # print("Entering input function")
    # _process_scheduled_events()
    # process_events()
    #
    # #print("Leaving input function")
    # if pin in _PIN_VALUES:
    #     return _PIN_VALUES[pin]
    # else:
    #     return 0
    # if sign == FALLING:
    #     if pin not in _FALLING_CALLBACKS:
    #         _FALLING_CALLBACKS[pin] = []
    #     _FALLING_CALLBACKS[pin].append(callback)
    # elif sign == RISING:
    #     if pin not in _RISING_CALLBACKS:
    #         _RISING_CALLBACKS[pin] = []
    #     _RISING_CALLBACKS[pin].append(callback)


class PWM:
    def __init__(self, arg, zup):
        pass

    def start(self, pho):
        pass

    def ChangeDutyCycle(self, i):
        pass

    def stop(self):
        pass
