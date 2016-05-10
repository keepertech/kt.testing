"""\
Support for faking out ``requests`` for tests.

Only requests specifically allowed will be permitted, with the responses
provided.

This does *not* intercede with other mechanisms for requesting resources
by URL from Python (httplib, urllib, urllib2, etc.).

"""

from __future__ import absolute_import

import errno
import json
import socket
import urlparse

import mock
import requests.structures
import urllib3


RESPONSE_ENTITY_NOT_ALLOWED = 204, 205, 301, 302, 303, 304, 307, 308


class Requests(object):

    def __init__(self, test, body='', content_type='text/plain'):
        self.test = test
        self.body = body
        self.content_type = content_type

    def setup(self):
        self.requests = []
        self.responses = {}

        p = mock.patch('requests.api.request', self.request)
        self.test.addCleanup(p.stop)
        p.start()

        p = mock.patch('requests.request', self.request)
        self.test.addCleanup(p.stop)
        p.start()

    def teardown(self):
        """The test failed if there were too many or too few requests."""
        if self.responses:
            raise AssertionError('configured responses not consumed')

    def add_error(self, method, url, exception, filter=None):
        assert isinstance(exception, Exception)
        self._add(method, url, filter, exception)

    def add_connect_timeout(self, method, url, filter=None):
        host = urlparse.urlsplit(url).hostname
        exception = requests.exceptions.Timeout(
            urllib3.exceptions.ConnectTimeoutError(
                None, 'Connection to %s out. (connect timeout=57.9)' % host))
        self._add(method, url, filter, exception)

    def add_read_timeout(self, method, url, filter=None):
        exception = requests.exceptions.Timeout(
            urllib3.exceptions.ReadTimeoutError(
                None, url, 'Read timed out. (read timeout=57.9)'))
        self._add(method, url, filter, exception)

    def add_unreachable_host(self, method, url, filter=None):
        reason = socket.error(errno.EHOSTUNREACH, 'No route to host')
        exception = requests.exceptions.ConnectionError(
            urllib3.exceptions.MaxRetryError(None, url, reason))
        self._add(method, url, filter, exception)

    def add_response(self, method, url, status=200, body=None, headers={},
                     filter=None):
        headers = requests.structures.CaseInsensitiveDict(headers)
        if status in RESPONSE_ENTITY_NOT_ALLOWED:
            if body:
                raise ValueError(
                    'cannot provide non-empty body for status == %s' % status)
            body = ''
        elif body is None:
            body = self.body
            headers['Content-Type'] = self.content_type
        self._add(method, url, filter, Response(status, body, headers))

    def _add(self, method, url, filter, response):
        key = method.upper(), url
        if filter is None:
            filter = always_allowed
        responses = self.responses.setdefault(key, [])
        responses.append((filter, response))

    def request(self, method, url, *args, **kwargs):
        key = method.upper(), url
        response = AssertionError('unexpected request: %s %s' % key)

        for i, (filter, resp) in enumerate(self.responses.get(key, ())):
            if filter(method, url, *args, **kwargs):
                del self.responses[key][i]
                if not self.responses[key]:
                    # All available responses have been consumed:
                    del self.responses[key]
                response = resp
                break

        self.requests.append((method, url, response, args, kwargs))
        if isinstance(response, Exception):
            raise response
        else:
            return response


def always_allowed(*args, **kwargs):
    return True


class Response(object):

    def __init__(self, status, text='', headers={}):
        headers = requests.structures.CaseInsensitiveDict(headers)
        if status in RESPONSE_ENTITY_NOT_ALLOWED:
            assert not text
        elif 'Content-Length' not in headers:
            headers['Content-Length'] = str(len(text))
        self.status_code = status
        self.text = text
        self.headers = headers

    def json(self):
        return json.loads(self.text)
