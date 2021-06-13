from adafruit_motorkit import MotorKit
from adafruit_blinka.agnostic import board_id, detector
import board
import busio

# if detector.board.any_embedded_linux:
#     from adafruit_blinka.microcontroller.generic_linux.i2c import I2C as _I2C
#     print("Embedded linux")
# elif detector.board.ftdi_ft2232h:
#     from adafruit_blinka.microcontroller.ftdi_mpsse.mpsse.i2c import I2C as _I2C
#     print("ftdi_mpsse")
# else:
#     from adafruit_blinka.microcontroller.generic_micropython.i2c import (
#         I2C as _I2C,
#     )
#     print("Generic microcontroller")
#
# print("Chip id:", detector.chip.id)
#
# _i2c = _I2C(10, mode=_I2C.MASTER, baudrate=100000)
#
#
# print(_i2c)
# print("SCL:", board.SCL)
# print("SDA:", board.SDA)
#
# i2c = busio.I2C(board.SCL, board.SDA)
# print(i2c.scan())
# i2c.deinit()
#
#
kit = MotorKit()

for i in range(100):
    kit.stepper1.onestep()
