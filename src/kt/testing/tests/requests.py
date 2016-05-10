"""\
Tests for kt.testing.requests.

"""

from __future__ import absolute_import

import errno
import socket
import unittest

import requests
import requests.api
import urllib3.exceptions

import kt.testing
import kt.testing.requests
import kt.testing.tests


class TestRequestsMethods(kt.testing.tests.Core, unittest.TestCase):

    api = requests

    def check_successful_run(self, cls, count=1):
        t, = self.loader.makeTest(cls)
        result = self.run_one_case(t)
        tc = t.test

        assert result.errors == []
        assert result.failures == []
        assert len(tc.fixture.requests) == count

        return tc

    def test_requests_get(self):

        class TC(object):

            api = self.api
            fixture = kt.testing.compose(kt.testing.requests.Requests)

            def setUp(self):
                super(TC, self).setUp()
                self.fixture.add_response('get', 'http://localhost:8000/foo')
                self.fixture.add_error('get', 'http://localhost:8000/foo',
                                       socket.gaierror('unknown name'))
                self.fixture.add_connect_timeout(
                    'get', 'http://localhost:8000/foo')
                self.fixture.add_read_timeout(
                    'get', 'http://localhost:8000/foo',
                    filter=lambda *a, **kw: True)
                self.fixture.add_unreachable_host(
                    'get', 'http://localhost:8000/foo')

            def testit(self):
                r = self.api.get('http://localhost:8000/foo')
                assert r.status_code == 200
                assert r.text == ''

                with self.assertRaises(socket.gaierror) as cm:
                    self.api.get('http://localhost:8000/foo')
                self.assertEqual(str(cm.exception), 'unknown name')

                with self.assertRaises(requests.exceptions.Timeout) as cm:
                    self.api.get('http://localhost:8000/foo')
                self.assertIsInstance(cm.exception.args[0],
                                      urllib3.exceptions.ConnectTimeoutError)

                with self.assertRaises(requests.exceptions.Timeout) as cm:
                    self.api.get('http://localhost:8000/foo')
                self.assertIsInstance(cm.exception.args[0],
                                      urllib3.exceptions.ReadTimeoutError)

                with self.assertRaises(
                        requests.exceptions.ConnectionError) as cm:
                    self.api.get('http://localhost:8000/foo')
                self.assertIsInstance(cm.exception.args[0],
                                      urllib3.exceptions.MaxRetryError)
                self.assertIsInstance(cm.exception.args[0].reason,
                                      socket.error)
                self.assertEqual(cm.exception.args[0].reason.errno,
                                 errno.EHOSTUNREACH)

        self.check_successful_run(TC, count=5)

    def test_requests_delete(self):
        self.check_requests_method('delete')

    def test_requests_patch(self):
        self.check_requests_method('patch')

    def test_requests_post(self):
        self.check_requests_method('post')

    def test_requests_put(self):
        self.check_requests_method('put')

    def check_requests_method(self, request_method):

        class TC(object):

            api = self.api
            method = request_method
            fixture = kt.testing.compose(kt.testing.requests.Requests)

            def setUp(self):
                super(TC, self).setUp()
                self.fixture.add_response(
                    self.method, 'http://localhost:8000/bar',
                    body='{"answer":42}',
                    headers={'Content-Type': 'application/json'})

            def testit(self):
                m = getattr(self.api, self.method)
                r = m('http://localhost:8000/bar')
                assert r.status_code == 200
                assert r.text == '{"answer":42}'
                assert r.json() == {'answer': 42}

        self.check_successful_run(TC)

    def test_empty_response_required(self):
        self.check_empty_response_required(204)
        self.check_empty_response_required(205)
        self.check_empty_response_required(301)
        self.check_empty_response_required(302)
        self.check_empty_response_required(303)
        self.check_empty_response_required(304)
        self.check_empty_response_required(307)
        self.check_empty_response_required(308)

    def check_empty_response_required(self, status):

        class TC(object):

            fixture = kt.testing.compose(kt.testing.requests.Requests)
            ran_testit = False

            def setUp(self):
                super(TC, self).setUp()
                self.fixture.add_response(
                    'get', 'http://localhost:8000/bar',
                    body='non-empty', status=status)

            def testit(self):
                self.ran_testit = True  # pragma: no cover

        t, = self.loader.makeTest(TC)
        result = self.run_one_case(t)
        tc = t.test

        (xt, err), = result.errors
        assert xt is t
        assert err.endswith(
            '\nValueError: cannot provide non-empty body for status == %s\n'
            % status)
        assert result.failures == []
        assert not tc.fixture.requests
        assert not tc.ran_testit

    def test_empty_response_allowed(self):
        self.check_empty_response_allowed(200)
        self.check_empty_response_allowed(201)
        self.check_empty_response_allowed(204)
        self.check_empty_response_allowed(205)
        self.check_empty_response_allowed(301)
        self.check_empty_response_allowed(302)
        self.check_empty_response_allowed(303)
        self.check_empty_response_allowed(304)
        self.check_empty_response_allowed(307)
        self.check_empty_response_allowed(308)
        self.check_empty_response_allowed(400)
        self.check_empty_response_allowed(404)
        self.check_empty_response_allowed(500)

    def check_empty_response_allowed(self, status):

        class TC(object):

            api = self.api
            fixture = kt.testing.compose(kt.testing.requests.Requests)
            ran_testit = False

            def setUp(self):
                super(TC, self).setUp()
                self.fixture.add_response(
                    'get', 'http://localhost:8000/bar',
                    body='', status=status)

            def testit(self):
                self.ran_testit = True
                r = self.api.get('http://localhost:8000/bar')
                assert r.status_code == status
                assert r.text == ''

        tc = self.check_successful_run(TC)
        assert tc.ran_testit

    def test_fails_without_matching_response(self):

        class TC(unittest.TestCase):

            fixture = kt.testing.compose(kt.testing.requests.Requests)

            def testit(self):
                pass  # pragma: no cover

        tc, = self.loader.makeTest(TC)
        tc = tc.test
        tc.setUp()

        try:
            try:
                self.api.get('http://www.python.org/')
            except AssertionError as e:
                e = str(e)
                assert e == 'unexpected request: GET http://www.python.org/'
            else:  # pragma: no cover
                raise AssertionError('expected AssertionError to be raised')
        finally:
            tc.tearDown()

    def test_multiple_responses(self):

        class TC(unittest.TestCase):

            fixture = kt.testing.compose(kt.testing.requests.Requests)

            def testit(self):
                pass  # pragma: no cover

        tc, = self.loader.makeTest(TC)
        tc = tc.test
        tc.setUp()
        tc.fixture.add_response(
            'get', 'http://www.keepertech.com/', body='first',
            headers={'content-length': '42'})
        tc.fixture.add_response(
            'get', 'http://www.keepertech.com/', body='second')

        # Responses for the same method/path are provided in the order
        # they are configured:

        try:
            r = self.api.get('http://www.keepertech.com/')
            assert r.status_code == 200
            assert r.text == 'first'
            assert int(r.headers['Content-Length']) == 42

            r = self.api.get('http://www.keepertech.com/')
            assert r.status_code == 200
            assert r.text == 'second'
        finally:
            tc.tearDown()

    def test_filtered_responses(self):

        class TC(unittest.TestCase):

            fixture = kt.testing.compose(kt.testing.requests.Requests)

            def testit(self):
                pass  # pragma: no cover

        tc, = self.loader.makeTest(TC)
        tc = tc.test
        tc.setUp()

        tc.fixture.add_response(
            'post', 'http://www.keepertech.com/', body='first',
            headers={'content-length': '42'},
            filter=(lambda *args, **kwargs:
                    'request 2' in kwargs.get('data')),
        )
        tc.fixture.add_response(
            'post', 'http://www.keepertech.com/', body='second',
            filter=(lambda *args, **kwargs:
                    'request 1' in kwargs.get('data')),
        )

        try:
            r = self.api.post('http://www.keepertech.com/',
                              data='some request 1 data')
            assert r.status_code == 200
            assert r.text == 'second'

            r = self.api.post('http://www.keepertech.com/',
                              data='some request 2 data')
            assert r.status_code == 200
            assert r.text == 'first'
            assert int(r.headers['Content-Length']) == 42
        finally:
            tc.tearDown()


class TestRequestsAPIMethods(TestRequestsMethods):
    """Anything that uses requests.* should be able to use requests.api.*.

    Verify the requests.api.* functions are handled by the fixture.

    """

    api = requests.api


class TestWithoutInvokingRequests(kt.testing.tests.Core, unittest.TestCase):

    # These tests don't cause any of the mocked APIs in requests to be
    # invoked, so they don't need to be performed for both requests.*
    # and requests.api.* flavors.

    def test_fails_if_responses_not_consumed(self):

        class TC(unittest.TestCase):

            fixture = kt.testing.compose(kt.testing.requests.Requests)

            def test_it(self):
                pass

        t, = self.loader.makeTest(TC)
        tc = t.test
        result = tc.defaultTestResult()

        tc.setUp()
        tc.fixture.add_response('get', 'http://www.keepertech.com/')
        tc.test_it()
        tc.tearDown()

        # If the test runs without consuming all the responses, an error
        # is generated during teardown:

        tc._resultForDoCleanups = result
        assert result.errors == []
        ok = tc.doCleanups()

        self.assertFalse(ok)
        (t, tb), = result.errors
        self.assertIn('configured responses not consumed', tb)
