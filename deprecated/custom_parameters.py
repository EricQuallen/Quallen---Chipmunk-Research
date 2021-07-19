"""
Support for a custom configuration file.

Currently unused.
"""

from typing import List, Dict


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
    def __init__(self, config_file):
        self.config_file = config_file
        self.parameters: List[Parameter] = []
        self.parameter_dict: Dict[str, Parameter] = {}

        # Parameters
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
        with open(self.config_file, 'w') as fh:
            for par in self.parameters:
                if len(par.exp) > 0:
                    fh.write("\n")
                    for line in par.exp.split("\n"):
                        fh.write("# ")
                        fh.write(line)
                        fh.write("\n")
                fh.write(par.name)
                fh.write("=")
                fh.write(par.value_as_string())
                fh.write("\n")

    def write_param(self):
        self.write_current_params()

    def read_from_file(self):
        print("Reading configuration file:", self.config_file, flush=True)
        try:
            with open(self.config_file, 'r') as fh:
                raw_lines = fh.readlines()  # read lines
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
            print("ERROR: Configuration file", self.config_file, "not found.")
            print("Creating new configuration file.")
            print("Please check the configuration and restart.")
            self.write_current_params()
            exit()
