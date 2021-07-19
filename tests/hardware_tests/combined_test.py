import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as mcp
from adafruit_mcp3xxx.analog_in import AnalogIn
from adafruit_motorkit import MotorKit

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D22)
mcp_3008 = mcp.MCP3008(spi, cs)
chan0 = AnalogIn(mcp_3008, mcp.P0)
chan1 = AnalogIn(mcp_3008, mcp.P1)

kit = MotorKit(address=96)
kit2 = MotorKit(address=97)

while True:
    val0, val1 = chan0.value, chan1.value
    if val0 > 100 and val1 <= 100:
        for i in range(1000):
            kit.stepper1.onestep()
    elif val1 > 100 and val0 <= 100:
        for i in range(1000):
            kit.stepper2.onestep()
    elif val0 > 100 and val1 > 100:
        for i in range(1000):
            kit2.stepper1.onestep()
    time.sleep(0.05)
