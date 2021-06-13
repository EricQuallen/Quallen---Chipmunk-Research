from adafruit_motorkit import MotorKit
import board

kit = MotorKit(i2c=board.I2C())

for i in range(100):
    kit.stepper1.onestep()
