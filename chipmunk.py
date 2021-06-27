# Import necessary libraries
import datetime  # For processing time stamps
import traceback  # For logging when the program crashes
import os  # For file reading
import json  # For reading the pin mapping
from typing import List, Dict, Optional

try:
    import RPi.GPIO as GPIO  # Input output pin controls
except ImportError:
    import Phony_RPi.GPIO as GPIO  # Input output pin controls

TEST_MODE = False
__version__ = "v1.0 06-27-2021"
__author__ = "J. Huizinga"

# Constants
ID = "ANIMALXXXX"
FOLDER = "./"
CONFIG_FILE = "ConfigurationFile.txt"
DATA_FILE = "results.txt"
ERROR_LOG = "error.txt"
LEGAL_ANSWERS = ["L", "M", "R", "A"]


# Functions
def custom_bool_cast(string: str):
    if string.lower() == "false":
        return False
    elif string == "0":
        return False
    else:
        return bool(string)


def parse_list_of_strings(string: str):
    return [sub_str.strip() for sub_str in string.split(",")]


def parse_list_of_lists_of_strings(string: str):
    return [parse_list_of_strings(lst) for lst in string.split(";")]


def write_list_of_list_of_strings(list_of_list):
    result = ""
    for i, list_of_strings in enumerate(list_of_list):
        for j, string in enumerate(list_of_strings):
            result += string
            if j < len(list_of_strings) - 1:
                result += ","
        if i < len(list_of_list) - 1:
            result += ";"
    return result


PARSE_DICT = {
    bool: custom_bool_cast,
    List[str]: parse_list_of_strings,
    List[List[str]]: parse_list_of_lists_of_strings,
}


WRITE_DICT = {
    List[List[str]]: write_list_of_list_of_strings
}


def log_error():
    print("WRITING ERROR LOG...")
    data_text = open(ERROR_LOG, 'w')  # open for appending
    data_text.write(traceback.format_exc())
    data_text.close()
    print("WRITING ERROR LOG DONE")


def cleanup():
    print("Cleanup")
    if LEDS is not None:
        LEDS.turn_all_off()
    GPIO.cleanup()


# Classes
class Parameter:
    def __init__(self, default, exp, par_type=int):
        self.name = None
        self.default = default
        self.exp = exp
        self.v = default
        self.par_type = par_type

    def set_from_string(self, value_as_string):
        if self.par_type in PARSE_DICT:
            self.v = PARSE_DICT[self.par_type](value_as_string)
        else:
            self.v = self.par_type(value_as_string)

    def value_as_string(self):
        if self.par_type in WRITE_DICT:
            return WRITE_DICT[self.par_type](self.v)
        else:
            return str(self.v)


class Parameters:
    def __init__(self):
        self.parameters: List[Parameter] = []
        self.parameter_dict: Dict[str, Parameter] = {}

        self.tests = Parameter(["A", "A", "A", "A", "L", "M", "R", ["M", "L"], ["M", "R"]],
                               "Tests to be given.",
                               List[List[str]])
        self._register_parameters()

    def _register_parameters(self):
        for name, param in self.__dict__.items():
            if isinstance(param, Parameter):
                param.name = name
                self.parameters.append(param)
                self.parameter_dict[name] = param

    def write_current_params(self):
        with open(CONFIG_FILE, 'w') as pFile:
            for par in self.parameters:
                if len(par.exp) > 0:
                    pFile.write("\n")
                    for line in par.exp.split("\n"):
                        pFile.write("# ")
                        pFile.write(line)
                        pFile.write("\n")
                pFile.write(par.name)
                pFile.write("=")
                pFile.write(par.value_as_string())
                pFile.write("\n")

    def write_param(self):
        self.write_current_params()

    def read_from_file(self):
        print("Reading configuration file:", CONFIG_FILE, flush=True)
        try:
            with open(CONFIG_FILE, 'r') as pFile:
                raw_lines = pFile.readlines()  # read lines
                # Remove comments and empty lines from lines
                for i, line in enumerate(raw_lines):
                    line = line.strip()
                    if len(line) == 0 or line[0] == "#":
                        continue
                    split_line = [x.strip() for x in line.split("=")]

                    assert len(split_line) == 2, f"Error reading configuration file on line {i}:\"{line}\". " \
                                                 f"Parameter lines need to be of the form " \
                                                 f"\"parameter_name = parameter_value\""
                    key, value = split_line
                    assert key in self.parameter_dict, f"Error reading configuration file on line {i}:\"{line}\". " \
                                                       f"Parameter {key} is not a known parameter."
                    self.parameter_dict[key].set_from_string(value)
        except FileNotFoundError:
            print("ERROR: Configuration file", CONFIG_FILE, "not found.")
            print("Creating new configuration file.")
            print("Please check the configuration and restart.")
            self.write_current_params()
            exit()


class PressurePads:
    def __init__(self, left_pressure_pad_pin, middle_pressure_pad_pin, right_pressure_pad_pin):
        self.push = None
        self.prev_push = None
        self.listen = False
        self.right_pressure_pad_pin = right_pressure_pad_pin
        self.middle_pressure_pad_pin = middle_pressure_pad_pin
        self.left_pressure_pad_pin = left_pressure_pad_pin

        # create the spi bus
        if TEST_MODE:
            from test_utilities import FakeAnalogIn as AnalogIn
            mcp = None
        else:
            try:
                import busio
                import digitalio
                import board
                import adafruit_mcp3xxx.mcp3008 as MCP
                from adafruit_mcp3xxx.analog_in import AnalogIn
                spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
                cs = digitalio.DigitalInOut(board.D22)
                mcp = MCP.MCP3008(spi, cs)
            except ImportError:
                from test_utilities import FakeAnalogIn as AnalogIn
                busio = None
                digitalio = None
                board = None
                MCP = None
                mcp = None

        self.right_pressure_pad_channel = AnalogIn(mcp, self.right_pressure_pad_pin)
        self.middle_pressure_pad_channel = AnalogIn(mcp, self.middle_pressure_pad_pin)
        self.left_pressure_pad_channel = AnalogIn(mcp, self.left_pressure_pad_pin)

        # Rough threshold to weight map:
        # 64 -> 20g
        # 128 -> 50g
        # 192-256 -> 70g
        self.left_threshold = 300
        self.middle_threshold = 200
        self.right_threshold = 100
        # self.threshold = 200

    def push_init(self):
        self.prev_push = self.push

    def push_poll(self):
        right_value = self.right_pressure_pad_channel.value
        middle_value = self.middle_pressure_pad_channel.value
        left_value = self.left_pressure_pad_channel.value
        right_pressure_pad_pressed = right_value > self.left_threshold
        middle_pressure_pad_pressed = middle_value > self.middle_threshold
        left_pressure_pad_pressed = left_value > self.right_threshold
        # print(f"registered values; left: {left_value}, middle {middle_value}, right {right_value}")
        if right_pressure_pad_pressed:
            self.push = "R"
        elif middle_pressure_pad_pressed:
            self.push = "M"
        elif left_pressure_pad_pressed:
            self.push = "L"
        else:
            self.push = None
        return self.push is None

    def push_wait(self):  # Monitor buttons and presence/absence
        self.push_init()
        # First wait until no pressure pads are pressed
        while not self.push_poll():
            pass
        # Then wait until one of pressure pads are pressed
        while self.push_poll():
            pass
        print("push = ", self.push)


class Conveyor:
    def __init__(self, stepper, steps_to_feed=1000, name=""):
        self.stepper = stepper
        self.steps_to_feed = steps_to_feed
        self.name = name

    def feed(self):
        print(f"Feeding from {self.name} conveyor")
        for i in range(self.steps_to_feed):
            self.stepper.onestep()


# JH: Class for keeping track of the LED status
class Leds:
    def __init__(self, left_led_pin, middle_led_pin, right_led_pin):
        self.left_led_pin = left_led_pin
        self.middle_led_pin = middle_led_pin
        self.right_led_pin = right_led_pin
        self.id_to_pin = {
            "L": self.left_led_pin,
            "M": self.middle_led_pin,
            "R": self.right_led_pin,
        }
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(left_led_pin, GPIO.OUT)
        GPIO.setup(middle_led_pin, GPIO.OUT)
        GPIO.setup(right_led_pin, GPIO.OUT)

    def turn_on(self, led_id):
        GPIO.output(self.id_to_pin[led_id], 1)

    def turn_off(self, led_id):
        GPIO.output(self.id_to_pin[led_id], 0)

    def turn_all_on(self):
        for pin in self.id_to_pin:
            self.turn_on(pin)

    def turn_all_off(self):
        for pin in self.id_to_pin:
            self.turn_off(pin)


LEDS: Optional[Leds] = None


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

        # Trial data
        self.answer_index: int = 0
        self.nb_correct_answers: int = 0
        self.nb_incorrect_answers: int = 0

        # Overall data
        self.rew_cnt: int = 0
        self.running: bool = True

    def testing_phase(self):
        if self.curr_test >= len(self.par.tests.v):
            self.running = False
            return
        answer_list = self.par.tests.v[self.curr_test]

        # Select answer
        answer = answer_list[self.answer_index]

        print("Test:", self.curr_test, " ", answer)

        time_start = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.pads.push_wait()  # Wait until one of the pressure pads is selected
        time_end = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.pads.push == answer or answer == "A":
            # if the animal got it right..
            print("Correct pad pressed", flush=True)
            self.nb_correct_answers += 1  # advance count of successful trials
            self.log_result(ID, "S", time_start, time_end, self.pads.push, answer)
            self.answer_index += 1
        elif self.pads.push != answer:
            print("Incorrect pad pressed", flush=True)
            self.nb_incorrect_answers += 1
            self.log_result(ID, "F", time_start, time_end, self.pads.push, answer)
            self.answer_index = 0

        if self.answer_index >= len(answer_list):
            self.test_success()

    def test_success(self):
        print("Test was successful")
        self.leds.turn_on(self.pads.push)
        self.conveyors[self.pads.push].feed()
        self.leds.turn_off(self.pads.push)
        self.rew_cnt += 1
        self.answer_index = 0
        self.curr_test += 1
        if self.curr_test > len(self.par.tests.v):
            self.running = False

    def log_result(self, animal_id, event, time1, time2, push, correct):
        # Build a data line and write it to memory
        data_list = [animal_id, event, time1, time2, self.curr_test,
                     self.answer_index, self.nb_incorrect_answers,
                     push, correct, self.rew_cnt]
        data_line = ','.join(map(str, data_list))  # transform list into a comma delinates string of values
        data_text = open(DATA_FILE, 'a')  # open for appending
        data_text.write(data_line + "\n")
        data_text.close()


def main():
    global LEDS
    with open(os.path.join(os.path.dirname(__file__), "pin_mapping.json")) as fh:
        pin_settings = json.load(fh)
    print("pin_settings:", pin_settings)
    parameters = Parameters()
    parameters.read_from_file()

    if TEST_MODE:
        import test_utilities
        from test_utilities import FakeMotorKit as MotorKit
        test_utilities.init()
    else:
        try:
            from adafruit_motorkit import MotorKit
        except ImportError:
            from test_utilities import FakeMotorKit as MotorKit
    kit1 = MotorKit(address=pin_settings["motor_kit_1_address"])
    kit2 = MotorKit(address=pin_settings["motor_kit_2_address"])
    kits = [kit1, kit2]

    conveyors = {
        "L": Conveyor(getattr(kits[pin_settings["left_conveyor_kit"]],
                              pin_settings["left_conveyor_stepper"]),
                      name="left"),
        "M": Conveyor(getattr(kits[pin_settings["middle_conveyor_kit"]],
                              pin_settings["middle_conveyor_stepper"]),
                      name="middle"),
        "R": Conveyor(getattr(kits[pin_settings["right_conveyor_kit"]],
                              pin_settings["right_conveyor_stepper"]),
                      name="right"),
    }
    pressure_pads = PressurePads(pin_settings["left_pressure_pad"],
                                 pin_settings["middle_pressure_pad"],
                                 pin_settings["right_pressure_pad"])
    leds = Leds(pin_settings["left_led"],
                pin_settings["middle_led"],
                pin_settings["right_led"])
    LEDS = leds
    experiment = Experiment(parameters, pressure_pads, conveyors, leds)

    while experiment.running:
        experiment.testing_phase()
    cleanup()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        cleanup()
    except KeyboardInterrupt:
        cleanup()
    except Exception as err:
        if err.args[0] == "exit request":
            cleanup()
        else:
            log_error()
            cleanup()
            raise
