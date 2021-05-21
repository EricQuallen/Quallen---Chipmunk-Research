# Import necessary libraries
try:
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    import RPi.GPIO as GPIO  # Input output pin controls
    TEST_MODE = False
except ModuleNotFoundError:
    import Phony_RPi.GPIO as GPIO
    TEST_MODE = True
import time  # For delays
import datetime  # For processing time stamps
import traceback  # For logging when the program crashes
import os  # For file reading
import json  # For reading the pin mapping
from typing import List, Dict

__version__ = "v0 08-05-2021"
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


PARSE_DICT = {
    bool: custom_bool_cast,
    List[str]: parse_list_of_strings,
    List[List[str]]: parse_list_of_lists_of_strings,
}


def log_error():
    print("WRITING ERROR LOG...")
    data_text = open(ERROR_LOG, 'w')  # open for appending
    data_text.write(traceback.format_exc())
    data_text.close()
    print("WRITING ERROR LOG DONE")


def cleanup():
    print("Cleanup")
    # TODO: Cleanup will probably have to be very different
    # GPIO.remove_event_detect(PRESSURE_PAD_LEFT)
    # GPIO.remove_event_detect(PRESSURE_PAD_MIDDLE)
    # GPIO.remove_event_detect(PRESSURE_PAD_RIGHT)
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
            parse_function = PARSE_DICT[self.par_type]
        else:
            parse_function = self.par_type
        self.v = parse_function(value_as_string)


class Parameters:
    def __init__(self):
        self.parameters: List[Parameter] = []
        self.parameter_dict: Dict[str, Parameter] = {}

        self.tests = Parameter("A; A; A; A; L; M; R; M,L; M,R",
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
                pFile.write(par.v)
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
                                                 f"Parameter lines need to be of the form \"parameter_name = parameter_value\""
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

        # TODO: This is where the pressure pad setup will happen
        GPIO.setup(right_pressure_pad_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(middle_pressure_pad_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(left_pressure_pad_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(right_pressure_pad_pin, GPIO.FALLING, callback=self.pushed, bouncetime=500)
        GPIO.add_event_detect(middle_pressure_pad_pin, GPIO.FALLING, callback=self.pushed, bouncetime=500)
        GPIO.add_event_detect(left_pressure_pad_pin, GPIO.FALLING, callback=self.pushed, bouncetime=500)

    def push_init(self):
        self.prev_push = self.push
        self.push = 0
        self.listen = 1  # respond to button push interrupts

    def push_poll(self):
        if self.push != 0:
            self.listen = 0  # stop listening to interrupts
            return False
        if TEST_MODE:
            GPIO.process_events()
        time.sleep(0.02)
        return True

    def push_wait(self):  # Monitor buttons and presence/absence
        self.push_init()
        while self.push_poll():
            pass  # this will monitor IR senor and the buttons
        print("push = ", self.push)

    def pushed(self, channel):  # interrupt detection function
        self.prev_push = self.push
        if self.listen == 1:  # Only do the following if we are listening...
            print("trigger detected...", flush=True)
            if channel == self.left_pressure_pad_pin:
                time.sleep(0.01)
                if GPIO.input(self.left_pressure_pad_pin) == 0:
                    self.push = "L"
                    self.listen = 0  # turn off listening for interrupts
            if channel == self.middle_pressure_pad_pin:
                time.sleep(0.01)
                if GPIO.input(self.middle_pressure_pad_pin) == 0:
                    self.push = "M"
                    self.listen = 0  # turn off listening for interrupts
            if channel == self.right_pressure_pad_pin:
                time.sleep(0.01)
                if GPIO.input(self.right_pressure_pad_pin) == 0:
                    self.push = "R"
                    self.listen = 0  # turn off listening for interrupts


class Conveyor:
    def __init__(self, pin_turn_motor_right, pin_turn_motor_left, pin_snap):
        self.pin_turn_motor_right = pin_turn_motor_right
        self.pin_turn_motor_left = pin_turn_motor_left
        self.pin_snap = pin_snap

        # TODO: This is where conveyor setup will happen
        # Input for motor snap switch. requires pull up enabled
        GPIO.setup(self.pin_snap, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Motor control - set high to turn motor right (facing spindle)
        GPIO.setup(self.pin_turn_motor_right, GPIO.OUT)
        # Motor control - set high to turn motor left (facing spindle)
        GPIO.setup(self.pin_turn_motor_left, GPIO.OUT)
        GPIO.output(self.pin_turn_motor_right, 0)  # motor in standby
        GPIO.output(self.pin_turn_motor_left, 0)  # motor in standby

    def feed(self):
        # Turn left
        GPIO.output(self.pin_turn_motor_left, 1)
        # Turn until for the "motor snap" to become active
        while GPIO.input(self.pin_snap) == 0:
            time.sleep(0.1)
        # Turn until for the "motor snap" to becomes inactive again
        while GPIO.input(self.pin_snap) == 1:
            time.sleep(0.05)
        # Stop turning
        GPIO.output(self.pin_turn_motor_left, 0)


class Experiment:
    def __init__(self,
                 parameters: Parameters,
                 pressure_pads: PressurePads,
                 conveyors: Dict[str, Conveyor]):
        self.par: Parameters = parameters
        self.pads: PressurePads = pressure_pads
        self.conveyors: Dict[str, Conveyor] = conveyors

        # Test parameters
        self.curr_test: int = 0
        # self.tests: List[List[str]] = []

        # Trial data
        self.answer_index: int = 0
        self.nb_correct_answers: int = 0
        self.nb_incorrect_answers: int = 0

        # Overall data
        self.rew_cnt: int = 0
        self.running: bool = True

    def testing_phase(self):
        print("Testing mode...")
        if self.curr_test > len(self.par.tests.v):
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
        self.conveyors[self.pads.push].feed()
        self.rew_cnt += 1
        self.answer_index = 0
        self.curr_test += 1
        if self.curr_test > len(self.par.tests.v):
            self.running = False

    def log_result(self, animal_id, event, time1, time2, push, correct):
        print("LOGGING...")
        # Build a data line and write it to memory
        data_list = [animal_id, event, time1, time2, self.curr_test,
                     self.answer_index, self.nb_incorrect_answers,
                     push, correct, self.rew_cnt]
        data_line = ','.join(map(str, data_list))  # transform list into a comma delinates string of values
        data_text = open(DATA_FILE, 'a')  # open for appending
        data_text.write(data_line + "\n")
        data_text.close()
        print("LOGGING DONE")


def main():
    # Setup GPIO interface to feeder, IR, etc.
    GPIO.setmode(GPIO.BCM)

    # TODO: These pin numbers are completely arbitrary
    with open(os.path.join(os.path.dirname(__file__), "pin_mapping.json")) as fh:
        pin_settings = json.load(fh)
    print("pin_settings:", pin_settings)
    conveyors = {
        "L": Conveyor(pin_settings["left_conveyor_turn_clockwise"],
                      pin_settings["left_conveyor_turn_counterclockwise"],
                      pin_settings["left_conveyor_sensor"]),
        "M": Conveyor(pin_settings["middle_conveyor_turn_clockwise"],
                      pin_settings["middle_conveyor_turn_counterclockwise"],
                      pin_settings["middle_conveyor_sensor"]),
        "R": Conveyor(pin_settings["right_conveyor_turn_clockwise"],
                      pin_settings["right_conveyor_turn_counterclockwise"],
                      pin_settings["right_conveyor_sensor"]),
    }
    parameters = Parameters()
    pressure_pads = PressurePads(pin_settings["left_pressure_pad"],
                                 pin_settings["middle_pressure_pad"],
                                 pin_settings["right_pressure_pad"])
    experiment = Experiment(parameters, pressure_pads, conveyors)

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
