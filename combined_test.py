import os
import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from adafruit_motorkit import MotorKit

kit = MotorKit(adress=96)
kit2 = MotorKit(address=97)

for i in range(100):
    kit.stepper1.onestep()
    kit.stepper2.onestep()
    kit2.stepper3.onestep()
