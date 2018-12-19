"""\
Tests for kt.testing.requests.

"""

from __future__ import absolute_import

import errno
import os
import socket
import unittest

import requests
import requests.api
import urllib3.exceptions

import kt.testing
import kt.testing.requests
import kt.testing.tests


class EmptyTC(kt.testing.TestCase):
    """Empty test case for tests where only setup/teardown matter.

    This is reasonable where we're testing the fixture component directly.

    """

    fixture = kt.testing.compose(kt.testing.requests.Requests)

    def testit(self):
        """Just a dummy."""


class TestRequestsMethods(kt.testing.tests.Core, unittest.TestCase):

    api = requests

    def check_successful_run(self, cls, count=1):
        tc, = self.loader.makeTest(cls)
        result = self.run_one_case(tc)

        assert result.errors == []
        assert result.failures == []
        assert len(tc.fixture.requests) == count

        return tc

    def test_requests_get(self):

        class TC(kt.testing.TestCase):

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

        class TC(kt.testing.TestCase):

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

        class TC(kt.testing.TestCase):

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
        tc = t

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

        class TC(kt.testing.TestCase):

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
                req = self.fixture.requests[-1]
                assert req.method == 'get'
                assert req[0] == 'get'
                assert req.url == 'http://localhost:8000/bar'
                assert req[1] == 'http://localhost:8000/bar'
                assert not req.body

        tc = self.check_successful_run(TC)
        assert tc.ran_testit

    def test_fails_without_matching_response(self):
        tc, = self.loader.makeTest(EmptyTC)
        tc.setUp()

        try:
            with self.assertRaises(AssertionError) as cm:
                self.api.get('http://www.python.org/')

            em = str(cm.exception)
            assert em == 'unexpected request: GET http://www.python.org/'
        finally:
            tc.tearDown()

    def test_fails_without_matching_response_json(self):
        self.check_fails_without_matching_response_json('patch')
        self.check_fails_without_matching_response_json('post')
        self.check_fails_without_matching_response_json('put')

    def check_fails_without_matching_response_json(self, method):
        tc, = self.loader.makeTest(EmptyTC)
        tc.setUp()
        msg = 'unexpected request: %s http://www.python.org/' % method.upper()
        meth = getattr(self.api, method)

        try:
            with self.assertRaises(AssertionError) as cm:
                meth('http://www.python.org/', json={'n': 42})
            em = str(cm.exception)
            assert msg in em
            # Verify normalized, pretty-printed, indented display is present:
            assert '\n    {\n      "n": 42\n    }' in em
            assert ' (pretty-printed for display)' in em
        finally:
            tc.tearDown()

    def test_fails_without_matching_response_json_as_data(self):
        self.check_fails_without_matching_response_json_as_data('patch')
        self.check_fails_without_matching_response_json_as_data('post')
        self.check_fails_without_matching_response_json_as_data('put')

    def check_fails_without_matching_response_json_as_data(self, method):
        tc, = self.loader.makeTest(EmptyTC)
        tc.setUp()
        msg = 'unexpected request: %s http://www.python.org/' % method.upper()
        meth = getattr(self.api, method)

        try:
            with self.assertRaises(AssertionError) as cm:
                meth('http://www.python.org/', data='{"n": 42}',
                     headers={'ConTent-tYPE': 'Application/Magic+JSON'})
            em = str(cm.exception)
            assert msg in em
            # Verify normalized, pretty-printed, indented display is present:
            assert '\n    Content-Type: Application/Magic+JSON' in em
            assert '\n    {\n      "n": 42\n    }' in em
            assert ' (pretty-printed for display)' in em
        finally:
            tc.tearDown()

    def test_fails_without_matching_response_malformed_json(self):
        self.check_fails_without_matching_response_malformed_json('patch')
        self.check_fails_without_matching_response_malformed_json('post')
        self.check_fails_without_matching_response_malformed_json('put')

    def check_fails_without_matching_response_malformed_json(self, method):
        tc, = self.loader.makeTest(EmptyTC)
        tc.setUp()
        msg = 'unexpected request: %s http://www.python.org/' % method.upper()
        meth = getattr(self.api, method)

        try:
            with self.assertRaises(AssertionError) as cm:
                meth('http://www.python.org/', data='{"n":',
                     headers={'ConTent-tYPE': 'Application/Magic+JSON'})
            em = str(cm.exception)
            assert msg in em
            assert '\n    Content-Type: Application/Magic+JSON' in em
            assert '\n    (malformed JSON data)' in em
        finally:
            tc.tearDown()

    def test_fails_without_matching_response_xml(self):
        self.check_fails_without_matching_response_xml('patch')
        self.check_fails_without_matching_response_xml('post')
        self.check_fails_without_matching_response_xml('put')

    def check_fails_without_matching_response_xml(self, method):
        tc, = self.loader.makeTest(EmptyTC)
        tc.setUp()
        msg = 'unexpected request: %s http://www.python.org/' % method.upper()
        meth = getattr(self.api, method)

        try:
            with self.assertRaises(AssertionError) as cm:
                meth('http://www.python.org/',
                     data='<pointy>brackets</pointy>',
                     headers={'ConTent-tYPE': 'Application/Magic+XML'})
            em = str(cm.exception)
            assert msg in em
            assert '\n    Content-Type: Application/Magic+XML' in em
            assert '\n    <pointy>brackets</pointy>' in em
        finally:
            tc.tearDown()

    def test_fails_without_matching_response_unhandled_ctype(self):
        self.check_fails_without_matching_response_unhandled_ctype('patch')
        self.check_fails_without_matching_response_unhandled_ctype('post')
        self.check_fails_without_matching_response_unhandled_ctype('put')

    def check_fails_without_matching_response_unhandled_ctype(self, method):
        tc, = self.loader.makeTest(EmptyTC)
        tc.setUp()
        msg = 'unexpected request: %s http://www.python.org/' % method.upper()
        meth = getattr(self.api, method)

        try:
            with self.assertRaises(AssertionError) as cm:
                meth('http://www.python.org/',
                     data=os.urandom(42),
                     headers={'ConTent-tYPE': 'Application/Octet-Stream'})
            em = str(cm.exception)
            assert msg in em
            assert '\n    Content-Type: Application/Octet-Stream' in em
            assert '\n    (content not shown)' in em
        finally:
            tc.tearDown()

    def test_fails_without_matching_response_missing_json(self):
        self.check_fails_without_matching_response_missing_json('patch')
        self.check_fails_without_matching_response_missing_json('post')
        self.check_fails_without_matching_response_missing_json('put')

    def check_fails_without_matching_response_missing_json(self, method):
        tc, = self.loader.makeTest(EmptyTC)
        tc.setUp()
        msg = 'unexpected request: %s http://www.python.org/' % method.upper()
        meth = getattr(self.api, method)

        try:
            with self.assertRaises(AssertionError) as cm:
                meth('http://www.python.org/',
                     headers={'ConTent-tYPE': 'Application/Magic+JSON'})
            em = str(cm.exception)
            assert msg in em
            assert '\n    Content-Type: Application/Magic+JSON' in em
            assert '\n    (undefined content)' in em
        finally:
            tc.tearDown()

    def test_multiple_responses(self):
        tc, = self.loader.makeTest(EmptyTC)
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
        tc, = self.loader.makeTest(EmptyTC)
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

    def test_iter_content_default_chunks(self):

        class TC(kt.testing.TestCase):

            fixture = kt.testing.compose(kt.testing.requests.Requests)

            def setUp(inst):
                super(TC, inst).setUp()
                inst.fixture.add_response(
                    'get', 'http://www.keepertech.com/', body='first')

            def testit(inst):
                resp = self.api.get('http://www.keepertech.com/', stream=True)
                inst.chunks = list(resp.iter_content())

        tc = self.check_successful_run(TC)
        self.assertEqual(tc.chunks, ['f', 'i', 'r', 's', 't'])

    def test_iter_content_specified_chunks(self):

        class TC(kt.testing.TestCase):

            fixture = kt.testing.compose(kt.testing.requests.Requests)

            def setUp(inst):
                super(TC, inst).setUp()
                inst.fixture.add_response(
                    'get', 'http://www.keepertech.com/', body='another')

            def testit(inst):
                resp = self.api.get('http://www.keepertech.com/', stream=True)
                inst.chunks = list(resp.iter_content(chunk_size=3))

        tc = self.check_successful_run(TC)
        self.assertEqual(tc.chunks, ['ano', 'the', 'r'])

    def test_fails_without_matching_after_filtering_one(self):

        def extra_setup(inst):
            inst.fixture.add_response(
                'put', 'http://www.keepertech.com/', body='first',
                filter=(lambda method, url, *args, **kwargs: False))

        exc = self.run_failing_case_with_setup(extra_setup)
        assert '\n    (filtered 1 prepared response)' in str(exc)

    def test_fails_without_matching_after_filtering_two(self):

        def extra_setup(inst):
            inst.fixture.add_response(
                'put', 'http://www.keepertech.com/', body='first',
                filter=(lambda method, url, *args, **kwargs: False))
            inst.fixture.add_response(
                'put', 'http://www.keepertech.com/', body='second',
                filter=(lambda method, url, *args, **kwargs: False))

        exc = self.run_failing_case_with_setup(extra_setup)
        assert '\n    (filtered 2 prepared responses)' in str(exc)

    def run_failing_case_with_setup(self, setup_function):

        class TC(kt.testing.TestCase):

            fixture = kt.testing.compose(kt.testing.requests.Requests)

            def setUp(inst):
                super(TC, inst).setUp()
                setup_function(inst)

            def testit(inst):
                self.api.put('http://www.keepertech.com/', data='stuff')

        tc, = self.loader.makeTest(TC)
        tc.setUp()
        try:
            with self.assertRaises(AssertionError) as cm:
                tc.testit()
        finally:
            tc.tearDown()

        return cm.exception


class TestRequestsAPIMethods(TestRequestsMethods):
    """Anything that uses requests.* should be able to use requests.api.*.

    Verify the requests.api.* functions are handled by the fixture.

    """

    api = requests.api


class TestRequestsSessionMethods(TestRequestsMethods):
    """Anything that uses requests.* should be able to use requests.api.*.

    Verify the requests.api.* functions are handled by the fixture.

    """

    def setUp(self):
        self.api = requests.Session()
        super(TestRequestsSessionMethods, self).setUp()


class TestRequestsDerivedSessionMethods(TestRequestsMethods):
    """Anything that uses requests.* should be able to use requests.api.*.

    Verify the requests.api.* functions are handled by the fixture.

    """

    class SpecialSession(requests.Session):
        special = True

    def setUp(self):
        self.api = self.SpecialSession()
        super(TestRequestsDerivedSessionMethods, self).setUp()


class TestWithoutInvokingRequests(kt.testing.tests.Core, unittest.TestCase):

    # These tests don't cause any of the mocked APIs in requests to be
    # invoked, so they don't need to be performed for both requests.*
    # and requests.api.* flavors.

    def test_fails_if_responses_not_consumed(self):

        class TC(kt.testing.TestCase):

            fixture = kt.testing.compose(kt.testing.requests.Requests)

            def setUp(self):
                super(TC, self).setUp()
                self.fixture.add_response('get', 'http://www.keepertech.com/')

            def test_it(self):
                pass

        tc, = self.loader.makeTest(TC)
        result = tc.defaultTestResult()

        # If the test runs without consuming all the responses, an error
        # is generated during teardown:
        #
        tc.run(result)

        # Uses failures in Python 3, errors in Python 2.
        (t, tb), = result.failures + result.errors
        self.assertIn('configured responses not consumed', tb)

    def get_response(self):
        return kt.testing.requests.Response(
            200, 'some text',
            headers={'content-type': 'text/plain; charset=utf-8'},
        )

    def test_request_info_attributes(self):
        response = self.get_response()

        ri = kt.testing.requests.RequestInfo(
            'get', 'http://localhost/path', response, (), {})

        self.assertIs(ri[0], ri.method)
        self.assertIs(ri[1], ri.url)
        self.assertIs(ri[2], ri.response)
        self.assertIs(ri[3], ri.args)
        self.assertIs(ri[4], ri.kwargs)
        self.assertIsNone(ri.body)
        self.assertIsNone(ri.headers)

    def test_request_info_repr(self):
        response = self.get_response()
        ri = kt.testing.requests.RequestInfo(
            'get', 'http://localhost/path', response, (), {})

        self.assertEqual(
            repr(ri),
            ("RequestInfo('get', 'http://localhost/path',"
             " <kt.testing.requests.Response 200>, (), {})"
             ))
