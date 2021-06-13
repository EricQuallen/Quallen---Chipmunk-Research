from adafruit_motorkit import MotorKit

kit = MotorKit(address = 0x61)

for i in range(100):
    kit.stepper1.onestep()
