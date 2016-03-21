"""\
Composition of test fixture components offering extended APIs.

"""

import sys
import unittest


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


class CompositeFixture(object):

    def __new__(cls, *args, **kwargs):
        self = super(CompositeFixture, cls).__new__(cls, *args, **kwargs)
        self._fixtures_by_marker = {}
        as_built = []
        for bcls in reversed(list(cls.mro())):
            if not issubclass(bcls, CompositeFixture):
                continue
            fixtures = getattr(bcls, '__fixtures__', ())
            for marker, factory, args, kwargs in fixtures:
                fixture = factory(self, *args, **kwargs)
                self._fixtures_by_marker[marker] = fixture
                as_built.append(fixture)
        self._fixtures_as_built = tuple(as_built)
        return self

    def setUp(self):
        for fixture in self._fixtures_as_built:
            fixture.setup()
            teardown = getattr(fixture, 'teardown', None)
            if teardown is not None:
                self.addCleanup(fixture.teardown)
        super(CompositeFixture, self).setUp()


class CFMeta(type):

    def __new__(cls, name, bases, content):
        compositor = CompositeFixture,
        foundation = unittest.TestCase,
        if bases == (object,):
            bases = ()
        else:
            for base in bases:
                if issubclass(base, CompositeFixture):
                    compositor = ()
                if issubclass(base, unittest.TestCase):
                    foundation = ()
        bases = compositor + bases + foundation

        if '__fixtures__' in content:
            content['__fixtures__'] = tuple(content['__fixtures__'])
        return super(CFMeta, cls).__new__(cls, name, bases, content)


def compose(factory, *args, **kwargs):
    depth = kwargs.pop('depth', 1)
    locals = sys._getframe(depth).f_locals
    if '__fixtures__' not in locals:
        locals['__fixtures__'] = []
    if '__metaclass__' in locals:
        # Verify compatible metaclass:
        cls = locals['__metaclass__']
        if not issubclass(cls, CFMeta):
            raise ValueError('competing metaclasses;'
                             ' found: %s.%s, need: %s.CFMeta'
                             % (cls.__module__, cls.__name__, __name__, ))
    else:
        locals['__metaclass__'] = CFMeta

    marker = object()
    locals['__fixtures__'].append((marker, factory, args, kwargs))
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
