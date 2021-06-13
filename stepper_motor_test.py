from adafruit_motorkit import MotorKit

kit = MotorKit(address = 97)

for i in range(100):
    kit.stepper1.onestep()
