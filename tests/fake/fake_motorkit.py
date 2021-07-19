class FakeStepper:
    def __init__(self, address, stepper_id):
        self.address = address
        self.id = stepper_id

    def onestep(self):
        pass


class FakeMotorKit:
    def __init__(self, address):
        self.address = address
        self.stepper1 = FakeStepper(address, 1)
        self.stepper2 = FakeStepper(address, 2)
