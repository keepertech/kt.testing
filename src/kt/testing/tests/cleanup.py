"""\
(c) 2018.  Keeper Technology LLC.  All Rights Reserved.
Use is subject to license.  Reproduction and distribution is strictly
prohibited.

Subject to the following third party software licenses and terms and
conditions (including open source):  www.keepertech.com/thirdpartylicenses

Tests for kt.testing.cleanup.

"""

import unittest

import kt.testing.cleanup
import kt.testing.tests


class CleanupHelpers(object):

    def setUp(self):
        super(CleanupHelpers, self).setUp()
        self.old_cleanups = list(kt.testing.cleanup._cleanups)
        del kt.testing.cleanup._cleanups[:]

    def tearDown(self):
        kt.testing.cleanup._cleanups[:] = self.old_cleanups
        super(CleanupHelpers, self).tearDown()


class CleanupTestCase(CleanupHelpers, unittest.TestCase):

    def test_register(self):

        def clean(*args, **kwargs):
            pass  # pragma: no cover

        kt.testing.cleanup.register(clean)
        kt.testing.cleanup.register(clean, 42, 24)
        kt.testing.cleanup.register(clean, one=1, two=2)
        kt.testing.cleanup.register(clean, 42, answer=42)

        r1, r2, r3, r4 = kt.testing.cleanup._cleanups

        self.assertEqual(r1, (clean, (), {}))
        self.assertEqual(r2, (clean, (42, 24), {}))
        self.assertEqual(r3, (clean, (), {'one': 1, 'two': 2}))
        self.assertEqual(r4, (clean, (42,), {'answer': 42}))

    def test_cleanup_empty(self):
        self.assertEqual(kt.testing.cleanup._cleanups, [])
        # Calling the cleanup function with no cleanups is perfectly ok;
        # it just doesn't do anything.
        kt.testing.cleanup.cleanup()
        self.assertEqual(kt.testing.cleanup._cleanups, [])

    def test_cleanup_in_order(self):
        self.assertEqual(kt.testing.cleanup._cleanups, [])
        calls = []

        def clean(index):
            calls.append(index)

        kt.testing.cleanup.register(clean, 0)
        kt.testing.cleanup.register(clean, 1)
        kt.testing.cleanup.register(clean, 2)
        kt.testing.cleanup.register(clean, 3)

        kt.testing.cleanup.cleanup()
        self.assertEqual(calls, [0, 1, 2, 3])

    def test_cleanup_exceptions_abort(self):
        self.assertEqual(kt.testing.cleanup._cleanups, [])
        calls = []

        def clean(index):
            calls.append(index)

        def bork(index):
            calls.append(index)
            raise ValueError('ugly failure')

        kt.testing.cleanup.register(clean, 0)
        kt.testing.cleanup.register(bork, 1)
        kt.testing.cleanup.register(clean, 2)

        with self.assertRaises(ValueError):
            kt.testing.cleanup.cleanup()
        self.assertEqual(calls, [0, 1])


class CleanupTestCaseTestCase(CleanupHelpers, kt.testing.tests.Core):

    def test_setup_teardown_both_clean_passing(self):
        self.assertEqual(kt.testing.cleanup._cleanups, [])
        calls = []

        def clean(index):
            calls.append(index)

        kt.testing.cleanup.register(clean, 0)
        kt.testing.cleanup.register(clean, 1)

        class TC(kt.testing.TestCase):

            def runTest(self):
                pass

        tc, = self.loader.makeTest(TC)

        self.assertEqual(calls, [])
        self.run_one_case(tc)
        self.assertEqual(calls, [0, 1, 0, 1])

    def test_setup_teardown_both_clean_failing(self):
        self.assertEqual(kt.testing.cleanup._cleanups, [])
        calls = []

        def clean(index):
            calls.append(index)

        kt.testing.cleanup.register(clean, 0)
        kt.testing.cleanup.register(clean, 1)

        class TC(kt.testing.TestCase):

            def runTest(self):
                self.fail('borken')

        tc, = self.loader.makeTest(TC)

        self.assertEqual(calls, [])
        self.run_one_case(tc)
        self.assertEqual(calls, [0, 1, 0, 1])
