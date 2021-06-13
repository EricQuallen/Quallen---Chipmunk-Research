from adafruit_motorkit import MotorKit

kit = MotorKit(i2c=1)

for i in range(100):
    kit.stepper1.onestep()
