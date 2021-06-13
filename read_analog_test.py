import os
import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

from adafruit_bus_device.spi_device import SPIDevice



print("The following pins are being used:")
print("Clock:", board.SCK)
print("MISO:", board.MISO)
print("MOSI:", board.MOSI)
print("Digital IO:", board.D22)
print("Analog:", MCP.P1)

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D22)


# _spi_device = SPIDevice(spi, cs)
# _out_buf = bytearray(3)
# _out_buf[0] = 0x01
# _in_buf = bytearray(3)
#
# for i in range(100):
#     with _spi_device as spi:
#         # pylint: disable=no-member
#         spi.write_readinto(_out_buf, _in_buf)
#         print("_out_buf:", _out_buf)
#         print("_in_buf:", _in_buf)
#         time.sleep(0.5)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on all pins that could possible be defined
chan0 = AnalogIn(mcp, MCP.P0)
chan1 = AnalogIn(mcp, MCP.P1)
# chan2 = AnalogIn(mcp, MCP.P2)
# chan3 = AnalogIn(mcp, MCP.P3)
# chan4 = AnalogIn(mcp, MCP.P4)
# chan5 = AnalogIn(mcp, MCP.P5)
# chan6 = AnalogIn(mcp, MCP.P6)
# chan7 = AnalogIn(mcp, MCP.P7)

print('Raw ADC Value channel 0: ', chan0.value)
print('ADC Voltage channel 0: ' + str(chan0.voltage) + 'V')
print('Raw ADC Value channel 1: ', chan1.value)
print('ADC Voltage channel 1: ' + str(chan1.voltage) + 'V')

while True:
    print("Channel 0:", chan0.value, "Channel 1:", chan1.value)
    time.sleep(0.5)
