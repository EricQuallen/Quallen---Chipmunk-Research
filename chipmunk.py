# Import necessary libraries
import datetime  # For processing time stamps
import traceback  # For logging when the program crashes
import os  # For file reading
from typing import List, Dict, Any
import time
import collections
import numpy as np
import argparse
import toml

__version__ = "v1.0 06-27-2021"
__author__ = "J. Huizinga"

# Files and folders
FOLDER = "./"
DEFAULT_CONFIG_FILE = "config_any_pad.toml"
DEVICE_CONFIGURATION_FILE = "device_configuration.toml"
RESULTS_FILE = "results.csv"
ERROR_LOG_FILE = "error.txt"

# Logging constants
LOG_ENTRIES = ["Animal ID",  # The ID of the animal (currently just a placeholder)
               "Waiting for press",  # Time when we started waiting for a press
               "Press start",  # Time when the press started
               "Press end",  # Time when the press ended
               "Test",  # The number of the test (if there is only one test, this will always be 0)
               "Test repeat",  # The number of times this test has been repeated
               "Answer index",  # For a test consisting of a sequence of pads, how far in the sequence we are
               "Provided answer",  # The answer (pressure pads pressed) given
               "Correct answer",  # The correct answer
               "Result",  # Result of the press
               "Incorrect answers",  # Total number of incorrect answers since the program was started
               "Correct answers",  # Total number of correct answers since the program was started
               "Left reward count",  # Number of rewards provided by the left conveyor
               "Middle reward count",  # Number of rewards provided by the middle conveyor
               "Right reward count",  # Number of rewards provided by the right conveyor
               "Total reward count"]  # Total number of rewards provided

ANIMAL_ID_PLACEHOLDER = "ANIMALXXXX"
CORRECT = "Correct"
INCORRECT = "Incorrect"
LEFT = "Left"
MIDDLE = "Middle"
RIGHT = "Right"
ANY = "Any"

# Other constants
TEST_PREFIX = 'test'


# Functions
def log_error():
    print("WRITING ERROR LOG...")
    data_text = open(ERROR_LOG_FILE, 'w')  # open for appending
    data_text.write(traceback.format_exc())
    data_text.close()
    print("WRITING ERROR LOG DONE")


# Classes
class Test:
    def __init__(self, answer, repeat=float('inf')):
        if isinstance(answer, str):
            answer = [answer]
        self.answer = answer
        self.repeat = repeat

    def to_dict(self):
        return {'answer': self.answer,
                'repeat': self.repeat}

    def __repr__(self):
        return f'Test({str(self.to_dict())})'


class Parameters:
    def __init__(self, config_file):
        self.parameter_dict: Dict[str, Any] = {}
        self.config_file = config_file

        # Parameters
        self.tests = [Test(answer=ANY)]

    def get_tests(self) -> List[Test]:
        return self.tests

    def _register(self, name, default):
        self.parameter_dict[name] = default
        return default

    def write_current_params(self):
        # Special case for tests
        for i, test in enumerate(self.tests):
            name = f'{TEST_PREFIX}{str(i+1)}'
            test.name = name
            self.parameter_dict[name] = test.to_dict()

        with open(self.config_file, 'w') as fh:
            toml.dump(self.parameter_dict, fh)

    def write_param(self):
        self.write_current_params()

    def read_from_file(self):
        print("Reading configuration file:", self.config_file, flush=True)
        try:
            with open(self.config_file, 'r') as fh:
                self.parameter_dict = toml.load(fh)
            tests = {}
            for name, value in self.parameter_dict.items():
                # Special case for tests
                if name.startswith(TEST_PREFIX):
                    test_index = int(name[len(TEST_PREFIX)])
                    tests[test_index] = value
                else:
                    self.__setattr__(name, value)

            self.tests = []
            for i in sorted(tests.keys()):
                self.tests.append(Test(**tests[i]))
            print(self.parameter_dict)

        except FileNotFoundError:
            print("ERROR: Configuration file", self.config_file, "not found.")
            print("Creating new configuration file.")
            print("Please check the configuration and restart.")
            self.write_current_params()
            exit()


class PressurePads:
    def __init__(self,
                 left_pressure_pad_pin,
                 middle_pressure_pad_pin,
                 right_pressure_pad_pin,
                 left_pressure_pad_threshold,
                 middle_pressure_pad_threshold,
                 right_pressure_pad_threshold,
                 read_frequency,
                 read_window,
                 test_mode=False,
                 verbose=False,
                 disable_left_pressure_pad=False,
                 disable_middle_pressure_pad=False,
                 disable_right_pressure_pad=True):
        self.push = None
        self.prev_push = None
        self.listen = False
        self.verbose = verbose
        self.right_pressure_pad_pin = right_pressure_pad_pin
        self.middle_pressure_pad_pin = middle_pressure_pad_pin
        self.left_pressure_pad_pin = left_pressure_pad_pin

        self.left_window = collections.deque(maxlen=read_window)
        self.middle_window = collections.deque(maxlen=read_window)
        self.right_window = collections.deque(maxlen=read_window)

        # create the spi bus
        if test_mode:
            from tests.fake import FakeAnalogIn as AnalogIn
            mcp_3008 = None
        else:
            import busio
            import digitalio
            import board
            import adafruit_mcp3xxx.mcp3008 as mcp
            from adafruit_mcp3xxx.analog_in import AnalogIn
            spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
            cs = digitalio.DigitalInOut(board.D22)
            mcp_3008 = mcp.MCP3008(spi, cs)

        if not disable_right_pressure_pad:
            self.right_pressure_pad_channel = AnalogIn(mcp_3008, self.right_pressure_pad_pin)
        else:
            self.right_pressure_pad_channel = None
        if not disable_middle_pressure_pad:
            self.middle_pressure_pad_channel = AnalogIn(mcp_3008, self.middle_pressure_pad_pin)
        else:
            self.middle_pressure_pad_channel = None
        if not disable_left_pressure_pad:
            self.left_pressure_pad_channel = AnalogIn(mcp_3008, self.left_pressure_pad_pin)
        else:
            self.left_pressure_pad_channel = None

        self.left_threshold = left_pressure_pad_threshold
        self.middle_threshold = middle_pressure_pad_threshold
        self.right_threshold = right_pressure_pad_threshold

        self.read_frequency = read_frequency
        self.read_window = read_window

    def push_init(self):
        self.prev_push = self.push

    def push_poll(self):
        if self.right_pressure_pad_channel is not None:
            right_value = self.right_pressure_pad_channel.value
        else:
            right_value = 0
        if self.middle_pressure_pad_channel is not None:
            middle_value = self.middle_pressure_pad_channel.value
        else:
            middle_value = 0
        if self.left_pressure_pad_channel is not None:
            left_value = self.left_pressure_pad_channel.value
        else:
            left_value = 0
        self.left_window.append(left_value)
        self.middle_window.append(middle_value)
        self.right_window.append(right_value)
        if self.verbose:
            print(f"registered values; left: {left_value}, middle {middle_value}, right {right_value}")

        time.sleep(1.0/self.read_frequency)
        if len(self.left_window) < self.read_window:
            self.push = None
            return False

        if self.verbose:
            print(f"mean values; left: {np.mean(self.left_window)}, "
                  f"middle {np.mean(self.middle_window)}, "
                  f"right {np.mean(self.right_window)}")

        left_pressure_pad_pressed = np.mean(self.left_window) > self.left_threshold
        middle_pressure_pad_pressed = np.mean(self.middle_window) > self.middle_threshold
        right_pressure_pad_pressed = np.mean(self.right_window) > self.right_threshold

        if right_pressure_pad_pressed:
            self.push = RIGHT
        elif middle_pressure_pad_pressed:
            self.push = MIDDLE
        elif left_pressure_pad_pressed:
            self.push = LEFT
        else:
            self.push = None

        return self.push is None

    def wait_release(self):
        self.push_init()
        while not self.push_poll():
            pass

    def push_wait(self):  # Monitor buttons and presence/absence
        self.push_init()
        # First wait until no pressure pads are pressed
        self.wait_release()
        # Then wait until one of pressure pads are pressed
        while self.push_poll():
            pass
        print("push = ", self.push)
        return self.push


class Conveyor:
    def __init__(self, stepper, steps_to_feed, name):
        self.stepper = stepper
        self.steps_to_feed = steps_to_feed
        self.name = name
        self.times_fed = 0

    def feed(self):
        print(f"Feeding from {self.name} conveyor")
        for i in range(self.steps_to_feed):
            self.stepper.onestep()
        self.times_fed += 1


# JH: Class for keeping track of the LED status
class Leds:
    def __init__(self, left_led_pin, middle_led_pin, right_led_pin, test_mode=False):
        self.left_led_pin = left_led_pin
        self.middle_led_pin = middle_led_pin
        self.right_led_pin = right_led_pin
        self.id_to_pin = {
            LEFT: self.left_led_pin,
            MIDDLE: self.middle_led_pin,
            RIGHT: self.right_led_pin,
        }

        if test_mode:
            # noinspection PyPackageRequirements,PyUnresolvedReferences
            import RPi.GPIO as GPIO  # Input output pin controls
        else:
            # noinspection PyPep8Naming
            import tests.fake.fake_gpio as GPIO  # Input output pin controls
        self.gpio = GPIO

    def turn_on(self, led_id):
        self.gpio.output(self.id_to_pin[led_id], 1)

    def turn_off(self, led_id):
        self.gpio.output(self.id_to_pin[led_id], 0)

    def turn_all_on(self):
        for pin in self.id_to_pin:
            self.turn_on(pin)

    def turn_all_off(self):
        for pin in self.id_to_pin:
            self.turn_off(pin)

    def setup(self):
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.setup(self.left_led_pin, self.gpio.OUT)
        self.gpio.setup(self.middle_led_pin, self.gpio.OUT)
        self.gpio.setup(self.right_led_pin, self.gpio.OUT)

    def cleanup(self):
        self.turn_all_off()
        self.gpio.cleanup()


class Experiment:
    def __init__(self,
                 parameters: Parameters,
                 pressure_pads: PressurePads,
                 conveyors: Dict[str, Conveyor],
                 leds: Leds):
        self.par: Parameters = parameters
        self.pads: PressurePads = pressure_pads
        self.conveyors: Dict[str, Conveyor] = conveyors
        self.leds = leds

        # Test parameters
        self.curr_test: int = 0
        self.test_repeat: int = 0

        # Trial data
        self.answer_index: int = 0
        self.nb_correct_answers: int = 0
        self.nb_incorrect_answers: int = 0

        # Overall data
        self.rew_cnt: int = 0
        self.running: bool = True

    def testing_phase(self):
        if self.curr_test >= len(self.par.get_tests()):
            self.running = False
            return
        answer_list = self.par.get_tests()[self.curr_test].answer
        answer = answer_list[self.answer_index]

        # Store for logging
        curr_test = self.curr_test
        test_repeat = self.test_repeat
        answer_index = self.answer_index

        print("Test:", self.curr_test, " ", answer)

        time_start = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        provided_answer = self.pads.push_wait()  # Wait until one of the pressure pads is selected
        time_end = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        result = None
        if provided_answer == answer or answer == ANY:
            # if the animal got it right..
            print("Correct pad pressed", flush=True)
            result = CORRECT
            self.nb_correct_answers += 1
            self.answer_index += 1
        elif provided_answer != answer:
            print("Incorrect pad pressed", flush=True)
            result = INCORRECT
            self.nb_incorrect_answers += 1
            self.answer_index = 0

        if self.answer_index >= len(answer_list):
            self.test_success(provided_answer)
        self.pads.wait_release()
        time_left_pad = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.log_result(result,
                        time_start,
                        time_end,
                        time_left_pad,
                        provided_answer,
                        answer,
                        curr_test,
                        answer_index,
                        test_repeat)

    def test_success(self, provided_answer):
        print("Test was successful")
        self.leds.turn_on(provided_answer)
        self.conveyors[provided_answer].feed()
        self.leds.turn_off(provided_answer)
        self.rew_cnt += 1
        self.answer_index = 0
        self.test_repeat += 1
        if self.test_repeat >= self.par.get_tests()[self.curr_test].repeat:
            self.curr_test += 1
            self.test_repeat = 0
        if self.curr_test > len(self.par.get_tests()):
            self.running = False

    def log_result(self, event, time1, time2, time_left_pad, push, correct, curr_test, answer_index, test_repeat):
        # Build a data line and write it to memory
        data = {"Animal ID": ANIMAL_ID_PLACEHOLDER,
                "Result": event,
                "Waiting for press": time1,
                "Press start": time2,
                "Press end": time_left_pad,
                "Test": curr_test,
                "Test repeat": test_repeat,
                "Answer index": answer_index,
                "Incorrect answers": self.nb_incorrect_answers,
                "Correct answers": self.nb_correct_answers,
                "Provided answer": push,
                "Correct answer": correct,
                "Left reward count": self.conveyors[LEFT].times_fed,
                "Middle reward count": self.conveyors[MIDDLE].times_fed,
                "Right reward count": self.conveyors[RIGHT].times_fed,
                "Total reward count": self.rew_cnt}
        data_list = [data[entry] for entry in LOG_ENTRIES]
        data_line = ','.join(map(str, data_list))  # transform list into a comma delineates string of values
        if not os.path.exists(RESULTS_FILE):
            header = ','.join(LOG_ENTRIES)
            with open(RESULTS_FILE, 'w') as fh:
                fh.write(header + "\n")
        with open(RESULTS_FILE, 'a') as fh:
            fh.write(data_line + "\n")

    def __enter__(self):
        self.leds.setup()

    def __exit__(self, exit_type, value, exit_traceback):
        self.leds.cleanup()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('configuration', metavar='C', type=str, nargs='?',
                        default=DEFAULT_CONFIG_FILE,
                        help='The configuration file to use')
    parser.add_argument('-t,--test-mode',
                        action='store_true',
                        dest='test_mode',
                        default=False,
                        help='Run the program in test-mode, making it possible '
                             'to the program without the actual device')
    parser.add_argument('-v,--verbose',
                        action='store_true',
                        default=False,
                        dest='verbose',
                        help='Print additional information to the terminal')
    args = parser.parse_args()

    with open(os.path.join(os.path.dirname(__file__), DEVICE_CONFIGURATION_FILE)) as fh:
        device_configuration = toml.load(fh)

    print('Device configuration:')
    for key, value in device_configuration.items():
        print(f'- {key}: {value}')

    parameters = Parameters(args.configuration)
    parameters.read_from_file()

    if args.test_mode:
        import tests.utilities
        from tests.fake import FakeMotorKit as MotorKit
        tests.utilities.init(DEVICE_CONFIGURATION_FILE)
    else:
        from adafruit_motorkit import MotorKit
    kit1 = MotorKit(address=device_configuration["motor_kit_1_address"])
    kit2 = MotorKit(address=device_configuration["motor_kit_2_address"])
    kits = [kit1, kit2]

    conveyors = {
        LEFT: Conveyor(getattr(kits[device_configuration["left_conveyor_kit"] - 1],
                               device_configuration["left_conveyor_stepper"]),
                       steps_to_feed=device_configuration["motor_steps"],
                       name="left"),
        MIDDLE: Conveyor(getattr(kits[device_configuration["middle_conveyor_kit"] - 1],
                                 device_configuration["middle_conveyor_stepper"]),
                         steps_to_feed=device_configuration["motor_steps"],
                         name="middle"),
        RIGHT: Conveyor(getattr(kits[device_configuration["right_conveyor_kit"] - 1],
                                device_configuration["right_conveyor_stepper"]),
                        steps_to_feed=device_configuration["motor_steps"],
                        name="right"),
    }
    pressure_pads = PressurePads(
        left_pressure_pad_pin=device_configuration["left_pressure_pad_pin"],
        middle_pressure_pad_pin=device_configuration["middle_pressure_pad_pin"],
        right_pressure_pad_pin=device_configuration["right_pressure_pad_pin"],
        left_pressure_pad_threshold=device_configuration["left_pressure_pad_threshold"],
        middle_pressure_pad_threshold=device_configuration["middle_pressure_pad_threshold"],
        right_pressure_pad_threshold=device_configuration["right_pressure_pad_threshold"],
        read_frequency=device_configuration["pressure_pad_read_frequency"],
        read_window=device_configuration["pressure_pad_read_window"],
        test_mode=args.test_mode,
        verbose=args.verbose)
    leds = Leds(device_configuration["left_led_pin"],
                device_configuration["middle_led_pin"],
                device_configuration["right_led_pin"])
    experiment = Experiment(parameters, pressure_pads, conveyors, leds)

    with experiment:
        while experiment.running:
            experiment.testing_phase()


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        if not err.args[0] == "exit request":
            log_error()
            raise
