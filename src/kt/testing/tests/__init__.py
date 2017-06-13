"""\
Support for kt.testing.tests.

"""

import unittest


class Core(unittest.TestCase):

    def setUp(self):
        # This is a mix-in; there should still be a setUp to be invoked.
        super(Core, self).setUp()
        self.loader = unittest.loader.TestLoader()
        self.loader.makeTest = self.loader.loadTestsFromTestCase

    def run_one_case(self, tc):
        self.result = tc.defaultTestResult()
        tc.run(result=self.result)
        assert self.result.testsRun == 1
        return self.result
