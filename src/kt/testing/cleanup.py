"""\
Support for registering cleanup functions for libraries, so they don't
have to be registered separately for every test.

This is heavily derived from ``zope.testing.cleanup``, but doesn't
require bringing in that library.  When available, the cleanups
registered with ``zope.testing.cleanup`` are used, and libraries
registering using ``kt.testing.cleanup`` will be cleaned up when a test
running uses ``zope.testing.cleanup`` instead.

"""

try:
    from zope.testing.cleanup import _cleanups
except ImportError:
    _cleanups = []


def register(func, *args, **kwargs):
    _cleanups.append((func, args, kwargs))


def cleanup():
    for func, args, kwargs in _cleanups:
        func(*args, **kwargs)
