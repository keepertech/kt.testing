"""\
Tests for kt.testing test fixture composition.

These tests use ``nose`` used for handling tests; something different
will be needed to ensure we work with other test runners.

"""

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


class TestComposition(kt.testing.tests.Core):

    def test_simple_usage(self):
        self.check_simple_usage(kt.testing.TestCase)

    def test_simple_usage_derived(self):

        class TC(kt.testing.TestCase):
            pass

        self.check_simple_usage(TC)

    def check_simple_usage(self, baseclass):

        class TC(baseclass):
            usingbase = kt.testing.compose(FixtureUsingBaseClass)
            independent = kt.testing.compose(IndependentFixture)

            record = []

            def test_this(self):
                self.record.append((self, 'test_this'))

            def test_the_other(self):
                self.record.append((self, 'test_the_other'))

        # Rely on tests being sorted in alphabetical order by method name.
        tto, tt = self.loader.makeTest(TC)
        tto_tc = tto
        tt_tc = tt

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

        class TCOne(kt.testing.TestCase):
            usingbase = kt.testing.compose(FixtureUsingBaseClass)

        class TCTwo(TCOne):
            independent = kt.testing.compose(IndependentFixture)
            record = []

            def test_this(self):
                self.record.append((self, 'test_this'))

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

    def test_case_can_use_fixture_api(self):

        class TC(kt.testing.TestCase):
            fixture = kt.testing.compose(IndependentFixture)
            record = []

            def test_this(self):
                self.record.append((self, 'test_this'))
                self.state = self.fixture.state
                self.fixture.complain('bleh')

        tt, = self.loader.makeTest(TC)
        result = self.run_one_case(tt)
        tt_record = [msg for tc, msg in TC.record]
        assert tt.state == tt.fixture.state

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

    def test_fixture_components_construction_args(self):

        class TC(kt.testing.TestCase):
            fixture = kt.testing.compose(IndependentFixture, 24)

        self.check_fixture_components_construction(TC)

    def test_fixture_components_construction_kwargs(self):

        class TC(kt.testing.TestCase):
            fixture = kt.testing.compose(IndependentFixture, state=24)

        self.check_fixture_components_construction(TC)

    def check_fixture_components_construction(self, cls):

        class TC(cls):
            record = []

            def test_this(self):
                self.state = self.fixture.state

        tt, = self.loader.makeTest(TC)
        self.run_one_case(tt)
        assert tt.state == 24

    # If the fixture component doesn't have a teardown method, it isn't
    # added to the cleanup list.

    def test_fixture_without_teardown(self):

        class TC(kt.testing.TestCase):
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

        class TCBase(kt.testing.TestCase):
            fixture = kt.testing.compose(IndependentFixture, state='original')

        class TC(TCBase):
            orig = TCBase.fixture
            fixture = kt.testing.compose(IndependentFixture, state='override')
            record = []

            def test_this(self):
                pass  # pragma: no cover

        tc, = self.loader.makeTest(TC)

        assert tc.orig.state == 'original'
        assert tc.fixture.state == 'override'

    def test_inherited_cooperative_setup(self):
        """\
        Co-operative setup is supported when appropriate bases are omitted.

        We do this because it's really important that our setUp method
        is invoked, so it should be drop-dead easy.

        """

        class TCBase(kt.testing.TestCase):

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
