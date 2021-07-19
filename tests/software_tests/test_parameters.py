import unittest
import chipmunk as cm


class TestParameters(cm.Parameters):
    def __init__(self, config_file):
        super().__init__(config_file)
        self.tests = [cm.Test(answer="A"),
                      cm.Test(answer="B"),
                      cm.Test(answer=["B", "C"])]
        self.param1 = self._register("param1", 1)
        self.param2 = self._register("param2", "test1")


class ParameterTestCase(unittest.TestCase):
    def test_parameters(self):
        print()
        params = TestParameters('test_config.toml')
        params.write_param()
        params.read_from_file()
        print(params.tests)


if __name__ == '__main__':
    unittest.main()
