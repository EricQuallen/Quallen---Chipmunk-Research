import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from adafruit_motorkit import MotorKit

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D22)
mcp = MCP.MCP3008(spi, cs)
chan0 = AnalogIn(mcp, MCP.P0)
chan1 = AnalogIn(mcp, MCP.P1)

kit = MotorKit(address=96)
kit2 = MotorKit(address=97)

while True:
    if chan0.value > 100:
        for i in range(1000):
            kit.stepper1.onestep()
    elif chan1.value > 100:
        for i in range(1000):
            kit2.stepper1.onestep()
    time.sleep(0.05)
