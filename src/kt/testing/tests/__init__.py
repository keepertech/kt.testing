"""\
Support for kt.testing.tests.

"""

import cStringIO
import nose.config
import nose.loader
import unittest


class Core(unittest.TestCase):

    def setUp(self):
        # This is a mix-in; there should still be a setUp to be invoked.
        super(Core, self).setUp()
        devnull = cStringIO.StringIO()
        config = nose.config.Config(logStream=devnull)
        self.loader = nose.loader.TestLoader(config=config)

    def run_one_case(self, tc):
        self.result = tc.defaultTestResult()
        tc.run(result=self.result)
        assert self.result.testsRun == 1
        return self.result
