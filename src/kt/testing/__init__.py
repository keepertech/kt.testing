"""\
Composition of test fixture components offering extended APIs.

"""

import sys
import unittest

import kt.testing.cleanup


class FixtureComponent(object):
    """Convenience base class for fixture components.

    Most users should only need to override the setup method.

    """

    def __init__(self, testcase):
        self.test = testcase

    def setup(self):
        pass

    def teardown(self):
        pass


class TestCase(unittest.TestCase):

    def __new__(cls, *args, **kwargs):
        new = super(TestCase, cls).__new__
        if new == object.__new__:
            self = new(cls)
        else:
            self = new(cls, *args, **kwargs)
        self._fixtures_by_marker = {}
        as_built = []
        for bcls in reversed(list(cls.mro())):
            if not issubclass(bcls, TestCase):
                continue
            fixtures = getattr(bcls, '__fixtures__', ())
            for marker, factory, args, kwargs in fixtures:
                fixture = factory(self, *args, **kwargs)
                self._fixtures_by_marker[marker] = fixture
                as_built.append(fixture)
        self._fixtures_as_built = tuple(as_built)
        return self

    def setUp(self):
        kt.testing.cleanup.cleanup()
        for fixture in self._fixtures_as_built:
            fixture.setup()
            teardown = getattr(fixture, 'teardown', None)
            if teardown is not None:
                self.addCleanup(fixture.teardown)
        super(TestCase, self).setUp()

    def tearDown(self):
        super(TestCase, self).tearDown()
        kt.testing.cleanup.cleanup()


def compose(factory, *args, **kwargs):
    depth = kwargs.pop('depth', 1)
    locals = sys._getframe(depth).f_locals
    if '__fixtures__' not in locals:
        locals['__fixtures__'] = ()

    marker = object()
    locals['__fixtures__'] += (marker, factory, args, kwargs),
    return _MarkerReference(marker, '_fixtures_by_marker')


class _MarkerReference(object):

    def __init__(self, marker, attribute):
        self.marker = marker
        self.attribute = attribute

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        # Get data by marker
        data = getattr(obj, self.attribute)
        return data[self.marker]
