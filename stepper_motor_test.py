from adafruit_motorkit import MotorKit
import board
import busio

i2c = busio.I2C(board.SCL, board.SDA)
print(i2c.scan())
i2c.deinit()


kit = MotorKit(i2c=board.I2C())

for i in range(100):
    kit.stepper1.onestep()
