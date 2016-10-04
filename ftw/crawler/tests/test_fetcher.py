from datetime import datetime
from ftw.crawler.configuration import Site
from ftw.crawler.exceptions import AttemptedRedirect
from ftw.crawler.exceptions import FetchingError
from ftw.crawler.exceptions import NotModified
from ftw.crawler.resource import ResourceInfo
from ftw.crawler.testing import FetcherTestCase
from ftw.crawler.tests.helpers import MockResponse
from ftw.crawler.utils import to_http_datetime
from ftw.crawler.utils import to_iso_datetime
from ftw.crawler.utils import to_utc
from mock import patch
from testfixtures import LogCapture
import logging
import shutil
import tempfile


class TestResourceFetcher(FetcherTestCase):

    def setUp(self):
        FetcherTestCase.setUp(self)
        self.tempdir = tempfile.mkdtemp(prefix='ftw.crawler.tests_')

    def tearDown(self):
        FetcherTestCase.tearDown(self)
        shutil.rmtree(self.tempdir)

    @patch('requests.sessions.Session.get')
    def test_fetches_and_saves_resource(self, request):
        request.return_value = MockResponse(
            content='MARKER', headers={'Content-Type': 'text/html'})
        resource_info = ResourceInfo(url_info={'loc': 'http://example.org/'})

        fetcher = self._create_fetcher(resource_info, tempdir=self.tempdir)
        resource_info = fetcher.fetch()

        self.assertTrue(resource_info.filename.startswith(self.tempdir))

        self.assertEquals('text/html', resource_info.content_type)
        with open(resource_info.filename) as resource_file:
            self.assertEquals('MARKER', resource_file.read())

    @patch('requests.sessions.Session.get')
    def test_returns_http_headers(self, request):
        request.return_value = MockResponse(
            content='', headers={'Content-Type': 'text/html'})
        resource_info = ResourceInfo(url_info={'loc': 'http://example.org/'})
        fetcher = self._create_fetcher(resource_info=resource_info)
        resource_info = fetcher.fetch()

        self.assertEquals({'Content-Type': 'text/html'}, resource_info.headers)

    @patch('requests.sessions.Session.get')
    def test_raises_if_not_200_ok(self, request):
        request.return_value = MockResponse(status_code=404)

        resource_info = ResourceInfo(url_info={'loc': 'http://example.org/'})
        fetcher = self._create_fetcher(resource_info)
        with self.assertRaises(FetchingError):
            fetcher.fetch()

    @patch('requests.sessions.Session.get')
    def test_sleeps_and_retries_when_too_many_requests(self, request):
        responses = [
            MockResponse(status_code=429),
            MockResponse(status_code=429),
            MockResponse(content='', headers={'Content-Type': 'text/html'}),
        ]
        request.side_effect = lambda url, **kw: responses.pop(0)

        resource_info = ResourceInfo(url_info={'loc': 'http://example.org/'},
                                     site=Site('http://example.org/'))
        fetcher = self._create_fetcher(resource_info)
        logging.disable(logging.INFO)
        with LogCapture() as log:
            resource_info = fetcher.fetch()

        log.check(('ftw.crawler.fetcher',
                   'WARNING',
                   u'429 Too Many Requests, sleeping for 0.1s'),
                  ('ftw.crawler.fetcher',
                   'WARNING',
                   u'429 Too Many Requests, sleeping for 0.2s'))

        self.assertEquals({'Content-Type': 'text/html'},
                          resource_info.headers)

    @patch('requests.sessions.Session.get')
    def test_raises_if_redirect(self, request):
        request.return_value = MockResponse(status_code=301, is_redirect=True)

        resource_info = ResourceInfo(url_info={'loc': 'http://example.org/'})
        fetcher = self._create_fetcher(resource_info)
        with self.assertRaises(AttemptedRedirect):
            fetcher.fetch()

    @patch('requests.sessions.Session.get')
    def test_doesnt_choke_on_charset_in_content_type(self, request):
        request.return_value = MockResponse(
            content='', headers={'Content-Type': 'text/html; charset=utf-8'})

        resource_info = ResourceInfo(url_info={'loc': 'http://example.org/'})
        fetcher = self._create_fetcher(resource_info)
        resource_info = fetcher.fetch()

        self.assertEquals('text/html', resource_info.content_type)


class TestFetcherIsModifiedLogic(FetcherTestCase):

    def _create_resource_info(self):
        return ResourceInfo(
            url_info={'loc': 'http://example.org/'},
            last_indexed=None)

    def test_unknown_last_indexed_time_always_yields_modified(self):
        fetcher = self._create_fetcher(self._create_resource_info())
        self.assertTrue(
            fetcher.is_modified(),
            "Unknown last_indexed time should result in resource being "
            "considered MODIFIED")

    def test_is_modified_tests_against_urlinfo_lastmod(self):
        resource_info = self._create_resource_info()
        fetcher = self._create_fetcher(resource_info)
        resource_info.last_indexed = to_utc(datetime(2014, 1, 1, 15, 30))

        server_modified = to_utc(datetime(2014, 1, 1, 15, 30))
        resource_info.url_info['lastmod'] = to_iso_datetime(server_modified)

        self.assertFalse(
            fetcher.is_modified(),
            "Equal modification dates should lead to resource being "
            "considered UNMODIFIED")

        server_modified = to_utc(datetime(2014, 1, 1, 15, 31))
        resource_info.url_info['lastmod'] = to_iso_datetime(server_modified)

        self.assertTrue(
            fetcher.is_modified(),
            "Newer server modification date should lead to resource being "
            "considered MODIFIED")

        server_modified = to_utc(datetime(2014, 1, 1, 15, 29))
        resource_info.url_info['lastmod'] = to_iso_datetime(server_modified)

        self.assertFalse(
            fetcher.is_modified(),
            "Older server modification date should lead to resource being "
            "considered UNMODIFIED")

    @patch('requests.sessions.Session.head')
    def test_is_modified_tests_against_http_last_modified(self, request):
        resource_info = self._create_resource_info()
        fetcher = self._create_fetcher(resource_info)
        resource_info.last_indexed = to_utc(datetime(2014, 1, 1, 15, 30))

        server_modified = to_utc(datetime(2014, 1, 1, 15, 30))
        request.return_value = MockResponse(
            headers={'last-modified': to_http_datetime(server_modified)})

        self.assertFalse(
            fetcher.is_modified(),
            "Equal modification dates should lead to resource being "
            "considered UNMODIFIED")

        server_modified = to_utc(datetime(2014, 1, 1, 15, 31))
        request.return_value = MockResponse(
            headers={'last-modified': to_http_datetime(server_modified)})

        self.assertTrue(
            fetcher.is_modified(),
            "Newer server modification date should lead to resource being "
            "considered MODIFIED")

        server_modified = to_utc(datetime(2014, 1, 1, 15, 29))
        request.return_value = MockResponse(
            headers={'last-modified': to_http_datetime(server_modified)})

        self.assertFalse(
            fetcher.is_modified(),
            "Older server modification date should lead to resource being "
            "considered UNMODIFIED")

    @patch('requests.sessions.Session.head')
    def test_is_modified_defaults_to_true(self, request):
        resource_info = self._create_resource_info()
        fetcher = self._create_fetcher(resource_info)
        resource_info.last_indexed = to_utc(datetime(2014, 1, 1, 15, 30))

        self.assertTrue(
            fetcher.is_modified(),
            "is_modified() should default to True if last_indexed date "
            "is present, but no server modification date could be determined")

    @patch('ftw.crawler.fetcher.ResourceFetcher.is_modified')
    @patch('requests.sessions.Session.get')
    def test_fetcher_doesnt_fetch_if_not_modified(self, request, is_modified):
        is_modified.return_value = False
        resource_info = self._create_resource_info()
        fetcher = self._create_fetcher(resource_info)
        with self.assertRaises(NotModified):
            fetcher.fetch()
        self.assertEquals(0, request.call_count)
