import time
import os
import json
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

with open(os.path.join(os.path.dirname(__file__), "pin_mapping.json")) as fh:
    pin_settings = json.load(fh)
print("pin_settings:", pin_settings)

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D22)
mcp = MCP.MCP3008(spi, cs)
left_pressure_pad = AnalogIn(mcp, pin_settings["left_pressure_pad"])
middle_pressure_pad = AnalogIn(mcp, pin_settings["middle_pressure_pad"])
right_pressure_pad = AnalogIn(mcp, pin_settings["right_pressure_pad"])

with open(os.path.join(os.path.dirname(__file__), "values.csv"), 'w') as fh:
    for i in range(1000):
        right_value = right_pressure_pad.value
        middle_value = middle_pressure_pad.value
        left_value = left_pressure_pad.value
        fh.write(f"{left_value},{middle_value},{right_value}\n")
        print(f"{i} registered values; left: {left_value}, middle {middle_value}, right {right_value}")
        time.sleep(0.01)
