=============================================
``kt.testing`` - Test harness support library
=============================================

Applications that make use of large frameworks often need to mock or
stub out portions of those APIs in ways that provide a consistent view
on the resources that API exposes.  A test fixture often wants to
establish a particular state for the API at a higher level than that of
individual API calls; this is especially the case if an API provides
more than one way to do things.  How the code under test uses the
underlying API is less interesting than the information exposed by the
API and the operations performed on it.

There are a number of ways to approach these situations using tests
based on ``unittest.TestCase`` (or similar) fixtures.  Too often, these
become tangled messes where test authors have to pay attention to
implementation details of base and mix-in classes to avoid support for
different APIs interfering with each other's internal state.

This library approaches the problem by allowing APIs that support test
control of other frameworks or libraries to be independent components.
These *fixture components* can:

- access the test object,

- be involved in setup and teardown,

- provide cleanup handlers,

- provide APIs for tests to configure the behavior of the APIs they
  manage, and

- provide additional assertion methods specific to what they do.

These components can inject themselves into the APIs they manage in
whatever ways are appropriate (using ``mock.patch``, for example).


Release history
---------------

1.1.0 (2016-05-10)
~~~~~~~~~~~~~~~~~~

New features:

- ``kt.testing.requests.Requests`` methods ``add_error`` and
  ``add_response`` grew a new, optional parameter, ``filter``, which
  accepts a callable wit the same signature as ``requests.request``.
  The result is a Boolean value that indicates whether request should be
  considered a match for the response.  The filter function will only be
  called if the method and URL match.

  This can be used to check whether request body matches some
  expectation.  This can be especially valuable for RPC-type interfaces
  (XML-RPC or SOAP, for example).

- New ``kt.testing.requests.Requests`` methods: ``add_connect_timeout``,
  ``add_read_timeout``, ``add_unreachable_host``, to add the
  corresponding exceptions to the set of configured responses.


1.0.0 (2016-03-21)
~~~~~~~~~~~~~~~~~~

Initial public release of library initialy created for internal use at
`Keeper Technology`_.


Implementing fixture components
-------------------------------

Fixture components are defined by a factory object, usually a class, and
are expected to provide a slim API for the harness.  Let's look at a
simple but complete, usable example::

  import logging


  class TestLoggingHandler(logging.StreamHandler):

      def __init__(self, stream, records):
          self.records = records
          super(TestLoggingHandler, self).__init__(stream)

      def handle(self, record):
          self.records.append(record)
          super(TestLoggingHandler, self).handle(record)


  class LoggingFixture(object):

      def __init__(self, test, name=None):
          self.test = test
          self.name = name

      def setup(self):
          sio = cStringIO.StringIO()
          self.output = sio.getvalue
          self.records = []
          handler = TestLoggingHandler(sio, self.records)
          logger = logging.getLogger(self.name)
          logger.addHandler(handler)
          self.test.addCleanup(logger.removeHandler, handler)

Using this from a test fixture is straightforward::

  import unittest


  class TestMyThing(unittest.TestCase):

      logging = kt.testing.compose(LoggingFixture)

      def test_some_logging(self):
          logging.getLogger('my.package').error('not happy')

          record = self.logging.records[-1]

          self.assertEqual(record.getMessage(), 'not happy')
          self.assertEqual(record.levelname, 'ERROR')

Fixture components may also provide a ``teardown`` method that takes no
arguments (aside from self).  These are called after the ``tearDown``
method of the test case is invoked, and do not require that method to be
successful.  (They are invoked as cleanup functions of the test case.)

Constructor arguments for the fixture component can be provided with
``kt.testing.compose``, but note that the test case instance will always
be passed as the first positional argument::

  class TestMyThing(unittest.TestCase):

      logging = kt.testing.compose(LoggingFixture, name='my.package')

      def test_some_logging(self):
          logging.getLogger('your.package').error('not happy')

          with self.assertRaises(IndexError):
              self.logging.records[-1]

Each instance of the test case class will get it's own instance of the
fixture components, accessible via the properties defined using
``kt.testing.compose``.  These instances will already be available when
the ``__init__`` method of the test case is invoked.

If the test class overrides the ``setUp`` method, it will need to ensure
the superclass ``setUp`` is invoked so the ``setup`` method of the
fixture components are invoked::

  class TestSomeThing(unittest.TestCase):

      logging = kt.testing.compose(LoggingFixture, name='my.package')

      def setUp(self):
          super(TestSomeThing, self).setUp()
          # more stuff here

Note that the ``setUp`` didn't invoke ``unittest.TestCase.setUp``
directly.  Since ``kt.testing.compose`` can cause an additional mix-in
class to be added, ``super`` is the way to go unless you're specifically
using a base class that's known to have the right mix-in already mixed.


Multiple fixtures and test inheritance
--------------------------------------

Multiple fixture components of the same or different types can be added
for a single test class::

  class TestMyThing(unittest.TestCase):

      my = kt.testing.compose(LoggingFixture, name='my.package')
      your = kt.testing.compose(LoggingFixture, name='your.package')

      def test_different(self):
          self.assertIsNot(self.my, self.your)

Base classes that use fixture components will be properly initialized,
and properties can be aliased and overridden in ways that make sense::

  class TestAnotherThing(TestMyThing):

      orig_my = TestMyThing.my
      my = kt.testing.compose(LoggingFixture, name='my.another')

      def test_different(self):
          self.assertIsNot(self.my, self.your)
          self.assertIsNot(self.orig_my, self.your)
          self.assertIsNot(self.orig_my, self.my)

          self.assertEqual(self.my.name, 'my.another')
          self.assertEqual(self.orig_my.name, 'my.package')
          self.assertEqual(self.your.name, 'your.package')


``kt.testing.requests`` - Intercession for ``requests``
-------------------------------------------------------

Many applications (and other libraries) use the ``requests`` package to
retrieve resources identified by URL.  It's often reasonable to use
``mock`` directly to handle requests for resources in tests, but
sometimes a little more is warranted.  The ``requests`` library provides
multiple ways to trigger particular requests, and applications usually
shouldn't care which is used to make a request.

A fixture component for ``requests`` is provided::

  class TestMyApplication(unittest.TestCase):

      requests = kt.testing.compose(kt.testing.requests.Requests)

A default response entity can be provided via constructor arguments
passed through ``compose``.  The body and content-type can both be
provided::

  class TestMyApplication(unittest.TestCase):

      requests = kt.testing.compose(
          kt.testing.requests.Requests,
          body='{"success": true, "value": "let's have some json data"}',
          content_type='application/json',
      )

If the default response entity is not defined, an empty body of type
text/plain is used.

The fixture provides these methods for configuring responses for
particular requests by URL:

``add_response(method, url, status=200, body=None, headers={})``
    Provide a particular response for a given URL and request method.
    Other aspects of the request are not considered for identifying what
    response to provide.

    If the response status indicates an entity is allowed in the
    response and `body` is provided as ``None``, the default body and
    content-type will be returned.  This will be an empty string unless
    some other value is provided to the fixture component constructor.
    If the status indicates no entity should be returned, an empty body
    will be used.

    The provided information will be used to create a response that is
    returned by the ``requests`` API.

``add_error(method, url, exception)``
    Provide an exception that should be raised when a particular
    resource is requested.  This can be used to simulate errors such as
    a non-responsive server or DNS resolution failure.  Only the URL and
    request method are considered for identifying what response to
    provide.

If a request is made that does match any provided response, an
``AssertionError`` is raised; this will normally cause a test to fail,
unless the code under test catches exceptions too aggressively.

A test that completes without consuming all configured responses will
cause an ``AssertionError`` to be raised during teardown.  Test runners
based on ``unittest`` will usually report this as an error rather than a
failure, but it'll require a developer to take a look, and that's the
point.

If multiple configurations are made for the same request method and URL
(whether responses or errors), they'll be provided to the application in
the order configured.


.. _Keeper Technology: http://www.keepertech.com/
