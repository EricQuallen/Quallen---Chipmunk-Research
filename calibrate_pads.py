import time
import os
import toml
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import numpy as np
from chipmunk import DEVICE_CONFIGURATION_FILE

with open(os.path.join(os.path.dirname(__file__), DEVICE_CONFIGURATION_FILE)) as fh:
    pin_settings = toml.load(fh)

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D22)
mcp = MCP.MCP3008(spi, cs)
left_pressure_pad = AnalogIn(mcp, pin_settings["left_pressure_pad_pin"])
middle_pressure_pad = AnalogIn(mcp, pin_settings["middle_pressure_pad_pin"])
right_pressure_pad = AnalogIn(mcp, pin_settings["right_pressure_pad_pin"])

left_values = []
middle_values = []
right_values = []

with open(os.path.join(os.path.dirname(__file__), "values.csv"), 'w') as fh:
    for i in range(1000):
        right_value = right_pressure_pad.value
        middle_value = middle_pressure_pad.value
        left_value = left_pressure_pad.value
        left_values.append(left_value)
        middle_values.append(middle_value)
        right_values.append(right_value)
        fh.write(f"{left_value},{middle_value},{right_value}\n")
        print(f"{i} registered values; left: {left_value}, middle {middle_value}, right {right_value}")

        time.sleep(0.01)

print("Left mean:", np.mean(np.array(left_values)), "var:", np.var(np.array(left_values)))
print("Middle mean:", np.mean(np.array(middle_values)), "var:", np.var(np.array(middle_values)))
print("Right mean:", np.mean(np.array(right_values)), "var:", np.var(np.array(right_values)))
