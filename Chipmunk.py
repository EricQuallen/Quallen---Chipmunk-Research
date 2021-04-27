# Import necessary libraries
try:
    import RPi.GPIO as GPIO  # Input output pin controls
except ImportError:
    import phony_gpio as GPIO
import time  # For delays
import datetime  # For processing time stamps
import collections  # Needed for making an ordered dictionary
import random  # For randomization and shuffling
import traceback  # For logging when the program crashes
from typing import List, Dict
import copy

# Puzzle box control system
__version__ = "v1 26-04-2021"
__author__ = "J. Huizinga"

# Constants
ID = "ANIMALXXXX"
FOLDER = "./"
CONFIG_FILE = "ConfigurationFile.txt"
DATA_FILE = "results.txt"
ERROR_LOG = "error.txt"
OPPOSITE_ANSWERS = {"R": "L", "L": "R", "X": "X"}
LEGAL_ANSWERS = ["L", "M", "R", "E", "I"]

# TODO: This should definitely be something completely different
PIN_MOTOR_SNAP = 20
PIN_MOTOR_RIGHT = 13
PIN_MOTOR_LEFT = 19
PRESSURE_PAD_RIGHT = 7
PRESSURE_PAD_MIDDLE = 6
PRESSURE_PAD_LEFT = 5


# Functions
def custom_bool_cast(string):
    if string.lower() == "false":
        return False
    elif string == "0":
        return False
    else:
        return bool(string)


def get_params():  # open the parameters file and get data
    parameters = Parameters()
    parameters.add_param("trials_in_block", 12, "Number of trials in a block")
    parameters.add_param("loop_test", 0, "Which test to loop back to after all are complete")
    parameters.add_param("block_suc_thresh", 9, "Block success threshold - minimum number of trials passed to move on")
    parameters.add_param("blocks_to_pass", 2, "Number of successive successful blocks to move to the next test")
    parameters.add_param("fail_delay", 5, "Fail delay - how many seconds to delay testing if an animal fails a trial")
    parameters.add_param("rew_max", 50, "Maximum number of reward allowed in a day")
    parameters.add_param("max_failed_blocks", 0, "Number of times a block can be failed before a long timeout.")
    parameters.add_param("failed_blocks_timout", 30, "Timeout when the maximum number of failed blocks is reached in minutes.")
    parameters.add_param("max_failed_trails", 0, "Number of trails that can be failed before a timeout (resets every block).")
    parameters.add_param("failed_trails_timeout", 60, "Timeout when the maximum number of failed trials is reached in seconds.")
    parameters.add_param("fail_trial_repeat", 0, "Number of times trial is repeated when a wrong answer is given.")
    parameters.add_param("consecutive_block", False, ": If set to True, enables consecutive block trails.", bool)
    parameters.add_named_param("tests", "shuffle1",
                               "The ordered sequence of tests to be performed. The answers\n"
                               "for each test should be defined on a separate line. For\n"
                               "example, if your test is named test1, you should define a\n"
                               "list of answers for that test as: test1=L-L, R-R\n"
                               "The special names \"rand,\"  and \"shuffle\"\n"
                               "can be used for random trial selection from the entire list.")
    parameters.add_named_param("shuffle1", "L-L, R-R",
                               "The lists of trials associated with each test. Each trial is an\n"
                               "answer-led pair, where the first character determines the correct\n"
                                "answer (“R” for right, “L” for left, “E” for either, “I” for\n"
                                "input, “S” for same as input, “O” opposite from input) and the\n"
                                "second character determines which LEDs will be on (“R” for right,\n"
                                "“L” for left, “B” for both, and “N” for neither)."
                               )
    return parameters


def feed_it():
    """
    Turn motor to administer food.
    """
    print("feeding")
    GPIO.output(PIN_MOTOR_RIGHT, 0)
    GPIO.output(PIN_MOTOR_LEFT, 1)  # Turn left
    while GPIO.input(PIN_MOTOR_SNAP) == 0:  # wait for switch
        time.sleep(0.1)
    while GPIO.input(PIN_MOTOR_SNAP) == 1:  # wait for switch
        time.sleep(0.05)
    GPIO.output(PIN_MOTOR_RIGHT, 0)
    GPIO.output(PIN_MOTOR_LEFT, 0)


def log_error():
    print("WRITING ERROR LOG...")
    data_text = open(ERROR_LOG, 'w')  # open for appending
    data_text.write(traceback.format_exc())
    data_text.close()
    print("WRITING ERROR LOG DONE")


def cleanup():
    print("Cleanup")
    # TODO: Cleanup will probably have to be very different
    GPIO.remove_event_detect(PRESSURE_PAD_LEFT)
    GPIO.remove_event_detect(PRESSURE_PAD_MIDDLE)
    GPIO.remove_event_detect(PRESSURE_PAD_RIGHT)
    GPIO.cleanup()


# Classes
class Parameter:
    def __init__(self, name, default, exp, par_type, positional):
        self.name = name
        self.default = default
        self.exp = exp
        self.positional = positional
        self.value = default
        self.par_type = par_type


class Parameters:
    def __init__(self):
        self.positionalParameters: List[Parameter] = []
        self.namedParameters: Dict[str, Parameter] = {}

    def write_current_params(self):
        with open(CONFIG_FILE, 'w') as pFile:
            for par in self.positionalParameters:
                if isinstance(par.value, int):
                    pFile.write(str(par.value).zfill(3))
                else:
                    pFile.write(str(par.value))
                pFile.write(" ")
                pFile.write(par.exp)
                pFile.write("\n")
            for par in self.namedParameters.values():
                if len(par.exp) > 0:
                    pFile.write("\n")
                    for line in par.exp.split("\n"):
                        pFile.write("# ")
                        pFile.write(line)
                        pFile.write("\n")
                pFile.write(par.name)
                pFile.write("=")
                pFile.write(par.value)
                pFile.write("\n")

    # JH: Changed how parameters are written
    def write_param(self):
        self.write_current_params()

    def reset_params(self):
        self.positionalParameters = []
        self.namedParameters = collections.OrderedDict()

    def add_param(self, name, default, exp, par_type=int):
        self.positionalParameters.append(Parameter(name, default, exp, par_type, True))

    def add_named_param(self, name, default, exp, par_type=str):
        self.namedParameters[name] = Parameter(name, default, exp, par_type, False)

    def read_from_file(self):
        # FIXME: This file-reading below is a mess
        # Read the configuration file, or write a new configuration file if it could
        # not be found.
        print("Reading configuration file:", CONFIG_FILE, flush=True)
        try:
            with open(CONFIG_FILE, 'r') as pFile:
                raw_lines = pFile.readlines()  # read lines
                pFile.close()
        except FileNotFoundError:
            print("ERROR: Configuration file", CONFIG_FILE, "not found.")
            print("Creating new configuration file.")
            print("Please check the configuration and restart.")
            self.write_current_params()
            exit()

        # Remove the values for the example parameters; read them from file instead
        self.namedParameters["tests"].value = ""
        del self.namedParameters["shuffle1"]

        # Remove comments and empty lines from lines
        lines = []
        for line in raw_lines:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == "#":
                continue
            lines.append(line)

        # Read positional parameters
        param = []
        lineIndex = 0
        while lineIndex < len(self.positionalParameters) and lineIndex < len(lines):
            print("Reading line:", lineIndex, ":", lines[lineIndex])
            parType = self.positionalParameters[lineIndex].par_type
            word = lines[lineIndex].split()[0]
            if parType == bool:
                value = custom_bool_cast(word)
            else:
                value = parType(word)
            param.append(value)
            lineIndex += 1
        ok = lineIndex == len(self.positionalParameters)
        if not ok:
            print("ERROR: Insufficient number of values found in configuration file.")
            exit()
        varNames = [par.name for par in self.positionalParameters]
        par = collections.OrderedDict(zip(varNames, param))

        # Read named parameters
        par["previous_shuffle"] = []
        tests = []
        testDict = dict()
        for i in range(lineIndex, len(lines)):
            line = lines[i].split("=")
            line = [x.strip() for x in line]
            key, values = line

            if key not in self.namedParameters:
                self.namedParameters[key] = Parameter(key, values, "", str, False)
            else:
                self.namedParameters[key].value = values

            if key == "tests":
                tests = values.split(",")
                tests = [x.strip() for x in tests]
            elif key == "previous_shuffle":
                par["previous_shuffle"] = values.split(",")
                par["previous_shuffle"] = [x.strip() for x in par["previous_shuffle"]]
            else:
                if len(testDict) == 0:
                    self.namedParameters[key].exp = ""
                testDict[key] = values.split(",")
                testDict[key] = [x.strip() for x in testDict[key]]
        slidingWindow = [0] * par['trials_in_block']


class PressurePads:
    def __init__(self):
        self.push = None
        self.prev_push = None
        self.listen = False

    def push_init(self):
        self.prev_push = self.push
        self.push = 0
        self.listen = 1  # respond to button push interrupts

    def push_poll(self):
        if self.push != 0:
            self.listen = 0  # stop listening to interrupts
            return False
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
            if channel == PRESSURE_PAD_LEFT:
                time.sleep(0.01)
                if GPIO.input(PRESSURE_PAD_LEFT) == 0:  # make sure it's a push and not a release
                    self.push = "L"
                    self.listen = 0  # turn off listening for interrupts
            if channel == PRESSURE_PAD_MIDDLE:
                time.sleep(0.01)
                if GPIO.input(PRESSURE_PAD_MIDDLE) == 0:  # make sure it's a push and not a release
                    self.push = "M"
                    self.listen = 0  # turn off listening for interrupts
            if channel == PRESSURE_PAD_RIGHT:
                time.sleep(0.01)
                if GPIO.input(PRESSURE_PAD_RIGHT) == 0:  # make sure it's a push and not a release
                    self.push = "R"
                    self.listen = 0  # turn off listening for interrupts


class Experiment:
    def __init__(self, parameters, pressure_pads):
        # FIXME: Parameters are currently unused
        self.par = parameters
        self.pads = pressure_pads

        self.curr_test: int = 0
        self.tests: List[str] = []
        self.testDict: Dict[str, List[str]] = {}
        self.previous_shuffle: List[str] = []

        # Trial data
        self.trial_cnt: int = 0
        self.trial_suc_cnt = 0
        self.trial_failed_cnt = 0
        self.current_trial_failed_cnt: int = 0
        self.trials_per_block = 1
        self.fail_trial_repeat = 0
        self.fail_trial_repeat = 0

        # Block data
        self.sliding_window = [0] * self.trials_per_block
        self.block_suc_thresh = 1
        self.consecutive_block = False
        self.curr_block = 0
        self.block_suc_cnt = 0
        self.blocks_to_pass = 1
        self.failed_blocks = 0
        self.max_failed_blocks = 1

        # Overall data
        self.loop_test = 0
        self.rew_cnt = 0
        self.prev_answer = "X"
        self.fail_delay = 0
        self.running = True

    def testing_phase(self):
        print("Testing mode...")
        if self.curr_test > len(self.tests):
            return
        test = self.tests[self.curr_test]

        # Select answer
        answer_list = self.testDict[test]
        if test.startswith("random"):
            answer = random.choice(answer_list)
        elif test.startswith("shuffle"):
            print("Shuffled tests list:",  self.previous_shuffle)
            reshuffle = (self.trial_cnt % len(answer_list) == 0) and self.current_trial_failed_cnt == 0
            if reshuffle or len(self.previous_shuffle) == 0:
                print("Shuffling tests")
                self.previous_shuffle = copy.copy(answer_list)
                random.shuffle(self.previous_shuffle)
                answer = self.previous_shuffle[0]
            else:
                print("Selecting next answer")
                answer = self.previous_shuffle[self.trial_cnt % len(self.previous_shuffle)]
        else:
            answer = answer_list[self.trial_cnt % len(answer_list)]

        print("Test:", test, " ", answer)
        if answer == "S":
            answer = self.prev_answer
        elif answer == "O":
            answer = OPPOSITE_ANSWERS[self.prev_answer]
        if answer not in LEGAL_ANSWERS:
            if answer == "X":
                answer = "I"
            else:
                raise Exception("Answer " + str(answer) + " not a legal answer. "
                                "Ensure the answer is in: " + str(LEGAL_ANSWERS))

        time_start = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.pads.push_wait()  # Wait until one of the pressure pads is selected
        time_end = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.pads.push == answer or answer == "E" or answer == "I":
            # if the animal got it right..
            print("test reward")
            feed_it()
            self.trial_suc_cnt += 1  # advance count of successful trials
            self.rew_cnt += 1  # advance total daily reward count
            self.current_trial_failed_cnt = 0
            self.sliding_window[self.trial_cnt % self.trials_per_block] = 1
            self.log_result(ID, "S", time_start, time_end, self.pads.push, answer)
            if answer == "I":
                self.prevAnswer = self.pads.push
        elif self.pads.push != answer:
            print("wrong. test failed", flush=True)
            self.trial_failed_cnt += 1
            self.current_trial_failed_cnt += 1
            self.sliding_window[self.trial_cnt % self.trials_per_block] = 0
            self.log_result(ID, "F", time_start, time_end, self.pads.push, answer)

        # JH: Trial count should be updated after logging, so the
        # correct number is logged
        self.trial_cnt += 1
        if self.consecutive_block:
            if sum(self.sliding_window) >= self.block_suc_thresh:
                self.block_success()
                self.end_block()
        elif self.trial_cnt >= self.trials_per_block:
            if self.trial_suc_cnt >= self.block_suc_thresh:
                self.block_success()
            else:
                self.block_fail()
            self.end_block()

    def end_block(self):
        print("Block ended")
        self.trial_cnt = 0
        self.curr_block += 1
        self.trial_failed_cnt = 0
        self.trial_suc_cnt = 0
        self.sliding_window = [0] * self.trials_per_block

    def block_success(self):
        print("Block was successfull")
        self.block_suc_cnt += 1
        if self.block_suc_cnt >= self.blocks_to_pass:
            self.curr_test += 1
            self.block_suc_cnt = 0
            if self.curr_test > len(self.tests) and self.loop_test > 0:
                self.curr_test = self.loop_test

    def block_fail(self):
        print("Block failed")
        self.failed_blocks += 1
        if self.failed_blocks >= self.max_failed_blocks and self.max_failed_blocks > 0:
            self.failed_blocks = 0

    def log_result(self, animal_id, event, time1, time2, push, correct):
        print("LOGGING...")
        # Build a data line and write it to memory
        data_list = [animal_id, event, time1, time2, self.curr_test, self.curr_block,
                 self.trial_cnt, self.current_trial_failed_cnt, self.trial_failed_cnt,
                 self.failed_blocks, push, correct, self.rew_cnt]
        data_line = ','.join(map(str, data_list))  # transform list into a comma delinates string of values
        data_text = open(DATA_FILE, 'a')  # open for appending
        data_text.write(data_line + "\n")
        data_text.close()
        print("LOGGING DONE")


def main():
    # TODO: previously used pygame, but I don't think that is necessary for this setup
    parameters = get_params()  # initialize parameters, just to avoid 'par not defined' errors
    pressure_pads = PressurePads()
    experiment = Experiment(parameters, pressure_pads)

    # Setup GPIO interface to feeder, IR, etc.
    GPIO.setmode(GPIO.BCM)

    # TODO: This is where the pressure pad setup will happen
    # Input for right screen button. requires pull up enabled
    GPIO.setup(PRESSURE_PAD_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Input for left screen button. requires pull up enabled
    GPIO.setup(PRESSURE_PAD_MIDDLE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Middle pressure pad
    GPIO.setup(PRESSURE_PAD_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # TODO: This is where we would have the callbacks for the pressure pads
    # Set up interrupts for when we are listening for button pushes on the monitor
    GPIO.add_event_detect(PRESSURE_PAD_RIGHT, GPIO.FALLING, callback=pressure_pads.pushed, bouncetime=500)
    GPIO.add_event_detect(PRESSURE_PAD_MIDDLE, GPIO.FALLING, callback=pressure_pads.pushed, bouncetime=500)
    GPIO.add_event_detect(PRESSURE_PAD_LEFT, GPIO.FALLING, callback=pressure_pads.pushed, bouncetime=500)

    # TODO: Probably still relevant in conveyor setup
    # Input for motor snap switch. requires pull up enabled
    GPIO.setup(PIN_MOTOR_SNAP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Motor control - set high to turn motor right (facing spindle)
    GPIO.setup(PIN_MOTOR_RIGHT, GPIO.OUT)
    # Motor control - set high to turn motor left (facing spindle)
    GPIO.setup(PIN_MOTOR_LEFT, GPIO.OUT)
    GPIO.output(PIN_MOTOR_RIGHT, 0)  # motor in standby
    GPIO.output(PIN_MOTOR_LEFT, 0)  # motor in standby

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
