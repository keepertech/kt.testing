"""\
Tests for kt.testing test fixture composition.

These tests use ``nose`` used for handling tests; something different
will be needed to ensure we work with other test runners.

"""

import unittest

import kt.testing
import kt.testing.tests


class FixtureUsingBaseClass(kt.testing.FixtureComponent):
    """Test fixture component derived from provided base class."""

    def __init__(self, testcase):
        super(FixtureUsingBaseClass, self).__init__(testcase)
        testcase.record.append((self.test, 'derived init'))

    def setup(self):
        super(FixtureUsingBaseClass, self).setup()
        self.test.record.append((self.test, 'derived setup'))
        self.test.addCleanup(
            lambda: self.test.record.append((self.test, 'derived cleanup')))

    def teardown(self):
        super(FixtureUsingBaseClass, self).teardown()
        self.test.record.append((self.test, 'derived teardown'))


class IndependentFixture(object):
    """Test fixture component not using provided base class."""

    def __init__(self, testcase, state=42):
        self.test = testcase
        testcase.record.append((self.test, 'independent init'))
        self.state = state

    def setup(self):
        self.test.record.append((self.test, 'independent setup'))
        self.test.addCleanup(
            lambda: self.test.record.append((self.test,
                                             'independent cleanup')))

    def teardown(self):
        self.test.record.append((self.test, 'independent teardown'))

    def complain(self, msg):
        self.test.record.append((self.test, 'independent complaint: %s' % msg))
        raise AssertionError('using independent class: %s' % msg)


class FixtureWithoutTeardown(object):

    def __init__(self, testcase):
        self.test = testcase
        testcase.record.append((self.test, 'teardownless init'))

    def setup(self):
        self.test.record.append((self.test, 'teardownless setup'))
        self.test.addCleanup(
            lambda: self.test.record.append((self.test,
                                             'teardownless cleanup')))


def unwrap(tc):
    """Retrieve test object from unittest.TestCase-derived nose test."""
    return tc.test


class TestComposition(kt.testing.tests.Core):

    def check_composite_case(self, cls):
        assert issubclass(cls, kt.testing.CompositeFixture)
        assert issubclass(cls, unittest.TestCase)

    def test_simple_usage(self):
        self.check_simple_usage(object)

    def test_simple_usage_testcase(self):
        self.check_simple_usage(unittest.TestCase)

    def check_simple_usage(self, baseclass):

        class TC(baseclass):
            usingbase = kt.testing.compose(FixtureUsingBaseClass)
            independent = kt.testing.compose(IndependentFixture)

            record = []

            def test_this(self):
                self.record.append((self, 'test_this'))

            def test_the_other(self):
                self.record.append((self, 'test_the_other'))

        self.check_composite_case(TC)

        # Rely on tests being sorted in alphabetical order by method name.
        tto, tt = self.loader.makeTest(TC)
        tto_tc = unwrap(tto)
        tt_tc = unwrap(tt)

        self.run_one_case(tto)
        tto_record = [msg for tc, msg in TC.record if tc is tto_tc]
        tt_record = [msg for tc, msg in TC.record if tc is tt_tc]
        assert tto_record == [
            'derived init',
            'independent init',
            'derived setup',
            'independent setup',
            'test_the_other',
            #
            # Note the intermixing of teardown and cleanups; the
            # teardowns for the fixture components are handled as
            # teardowns for the test itself.
            #
            'independent teardown',
            'independent cleanup',
            'derived teardown',
            'derived cleanup',
        ]
        # The fixture components have already been created for test_this
        # as well, but the setup methods haven't been called:
        assert tt_record == [
            'derived init',
            'independent init',
        ]

        self.run_one_case(tt)
        tt_record = [msg for tc, msg in TC.record if tc is tt_tc]
        assert tt_record == [
            'derived init',
            'independent init',
            'derived setup',
            'independent setup',
            'test_this',
            'independent teardown',
            'independent cleanup',
            'derived teardown',
            'derived cleanup',
        ]

    def test_inherited_fixture_components(self):
        self.check_inherited_fixture_components(object)

    def test_inherited_fixture_components_testcase(self):
        self.check_inherited_fixture_components(unittest.TestCase)

    def check_inherited_fixture_components(self, baseclass):

        class TCOne(baseclass):
            usingbase = kt.testing.compose(FixtureUsingBaseClass)

        class TCTwo(TCOne):
            independent = kt.testing.compose(IndependentFixture)
            record = []

            def test_this(self):
                self.record.append((self, 'test_this'))

        self.check_composite_case(TCOne)
        self.check_composite_case(TCTwo)

        tt, = self.loader.makeTest(TCTwo)

        self.run_one_case(tt)
        tt_record = [msg for tc, msg in TCTwo.record]
        assert tt_record == [
            'derived init',
            'independent init',
            'derived setup',
            'independent setup',
            'test_this',
            'independent teardown',
            'independent cleanup',
            'derived teardown',
            'derived cleanup',
        ]

    def test_explicit_derived_metaclass_allowed(self):

        class DerivedMeta(kt.testing.CFMeta):
            pass

        self.check_explicit_metaclass_allowed(DerivedMeta)

    def test_explicit_metaclass_allowed(self):
        self.check_explicit_metaclass_allowed(kt.testing.CFMeta)

    def check_explicit_metaclass_allowed(self, meta):

        class TC(object):
            __metaclass__ = meta
            fixture = kt.testing.compose(IndependentFixture)
            record = []

            def test_this(self):
                self.record.append((self, 'test_this'))

        self.check_composite_case(TC)

        tt, = self.loader.makeTest(TC)

        self.run_one_case(tt)
        tt_record = [msg for tc, msg in TC.record]
        assert tt_record == [
            'independent init',
            'independent setup',
            'test_this',
            'independent teardown',
            'independent cleanup',
        ]

    def test_conflicting_metaclass_disallowed(self):

        class AltMeta(type):
            pass

        try:
            class TC(object):
                __metaclass__ = AltMeta

                kt.testing.compose(IndependentFixture)
        except ValueError as e:
            assert str(e) == ('competing metaclasses;'
                              ' found: kt.testing.tests.composite.AltMeta,'
                              ' need: kt.testing.CFMeta')
        else:  # pragma: no cover
            raise AssertionError('expected ValueError')

    def test_metaclass_used_without_fixtures_allowed(self):
        self.check_explicit_metaclass_without_fixtures_allowed(
            kt.testing.CFMeta)

    def test_derived_metaclass_used_without_fixtures_allowed(self):

        class DerivedMeta(kt.testing.CFMeta):
            pass

        self.check_explicit_metaclass_without_fixtures_allowed(DerivedMeta)

    def check_explicit_metaclass_without_fixtures_allowed(self, meta):
        # Unlikely, but harmless.

        class TC(object):
            __metaclass__ = meta
            record = []

            def test_this(self):
                self.record.append((self, 'test_this'))

        self.check_composite_case(TC)

        tt, = self.loader.makeTest(TC)

        self.run_one_case(tt)
        tt_record = [msg for tc, msg in TC.record]
        assert tt_record == ['test_this']

    def test_test_can_use_fixture_api(self):
        self.check_case_can_use_fixture_api(object)

    def test_test_can_use_fixture_api_testcase(self):
        self.check_case_can_use_fixture_api(unittest.TestCase)

    def check_case_can_use_fixture_api(self, base):

        class TC(base):
            fixture = kt.testing.compose(IndependentFixture)
            record = []

            def test_this(self):
                self.record.append((self, 'test_this'))
                self.state = self.fixture.state
                self.fixture.complain('bleh')

        tt, = self.loader.makeTest(TC)
        result = self.run_one_case(tt)
        tt_record = [msg for tc, msg in TC.record]
        assert unwrap(tt).state == unwrap(tt).fixture.state

        assert tt_record == [
            'independent init',
            'independent setup',
            'test_this',
            'independent complaint: bleh',
            'independent teardown',
            'independent cleanup',
        ]

        (xtc, err), = result.failures
        assert xtc is tt
        assert err.startswith('Traceback (most recent call last):')
        assert 'using independent class: bleh' in err

    def test_fixture_components_get_args(self):
        self.check_fixture_components_construction_args(object)

    def test_fixture_components_get_args_testcase(self):
        self.check_fixture_components_construction_args(unittest.TestCase)

    def test_fixture_components_get_kwargs(self):
        self.check_fixture_components_construction_kwargs(object)

    def test_fixture_components_get_kwargs_testcase(self):
        self.check_fixture_components_construction_kwargs(unittest.TestCase)

    def check_fixture_components_construction_args(self, base):

        class TC(base):
            fixture = kt.testing.compose(IndependentFixture, 24)

        self.check_fixture_components_construction(TC)

    def check_fixture_components_construction_kwargs(self, base):

        class TC(base):
            fixture = kt.testing.compose(IndependentFixture, state=24)

        self.check_fixture_components_construction(TC)

    def check_fixture_components_construction(self, cls):

        class TC(cls):
            record = []

            def test_this(self):
                self.state = self.fixture.state

        tt, = self.loader.makeTest(TC)
        self.run_one_case(tt)
        assert unwrap(tt).state == 24

    # If the fixture component doesn't have a teardown method, it isn't
    # added to the cleanup list.

    def test_fixture_without_teardown(self):
        self.check_fixture_without_teardown(object)

    def test_fixture_without_teardown_testcase(self):
        self.check_fixture_without_teardown(unittest.TestCase)

    def check_fixture_without_teardown(self, base):

        class TC(base):
            fixture = kt.testing.compose(FixtureWithoutTeardown)
            record = []

            def test_this(self):
                self.record.append((self, 'test_this'))

        tt, = self.loader.makeTest(TC)
        self.run_one_case(tt)
        tt_record = [msg for tc, msg in TC.record]

        assert tt_record == [
            'teardownless init',
            'teardownless setup',
            'test_this',
            'teardownless cleanup',
        ]

    # Overriding a fixture component property doesn't make the component
    # inaccessible; aliases for component properties work just fine.

    def test_component_property_alias(self):
        self.check_component_property_alias(object)

    def test_component_property_alias_testcase(self):
        self.check_component_property_alias(unittest.TestCase)

    def check_component_property_alias(self, base):

        class TCBase(base):
            fixture = kt.testing.compose(IndependentFixture, state='original')

        class TC(TCBase):
            orig = TCBase.fixture
            fixture = kt.testing.compose(IndependentFixture, state='override')
            record = []

            def test_this(self):
                pass  # pragma: no cover

        tt, = self.loader.makeTest(TC)
        tc = unwrap(tt)

        assert tc.orig.state == 'original'
        assert tc.fixture.state == 'override'

    def test_inherited_cooperative_setup(self):
        self.check_inherited_cooperative_setup(object)

    def test_inherited_cooperative_setup_testcase(self):
        self.check_inherited_cooperative_setup(unittest.TestCase)

    def check_inherited_cooperative_setup(self, base):
        """\
        Co-operative setup is supported when appropriate bases are omitted.

        We do this because it's really important that our setUp method
        is invoked, so it should be drop-dead easy.

        """

        class TCBase(base):

            # No fixture composition here.

            def setUp(self):
                super(TCBase, self).setUp()
                self.record.append((self, 'TCBase setup'))

        class TC(TCBase):

            fixture = kt.testing.compose(FixtureWithoutTeardown)
            record = []

            def test_this(self):
                self.record.append((self, 'test_this'))

        tt, = self.loader.makeTest(TC)
        self.run_one_case(tt)
        tt_record = [msg for tc, msg in TC.record]

        assert tt_record == [
            'teardownless init',
            'teardownless setup',
            'TCBase setup',
            'test_this',
            'teardownless cleanup',
        ]
