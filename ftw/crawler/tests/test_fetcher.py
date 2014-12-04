from ftw.crawler.exceptions import FetchingError
from ftw.crawler.fetcher import ResourceFetcher
from ftw.crawler.resource import ResourceInfo
from ftw.crawler.tests.helpers import MockResponse
from mock import patch
from unittest2 import TestCase
import requests
import shutil
import tempfile


class TestResourceFetcher(TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix='ftw.crawler.tests_')

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def _create_fetcher(self, resource_info=None, session=None, tempdir=None):
        if resource_info is None:
            resource_info = ResourceInfo()

        if session is None:
            session = requests.Session()

        return ResourceFetcher(
            resource_info=resource_info, session=session, tempdir=tempdir)

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
    def test_doesnt_choke_on_charset_in_content_type(self, request):
        request.return_value = MockResponse(
            content='', headers={'Content-Type': 'text/html; charset=utf-8'})

        resource_info = ResourceInfo(url_info={'loc': 'http://example.org/'})
        fetcher = self._create_fetcher(resource_info)
        resource_info = fetcher.fetch()

        self.assertEquals('text/html', resource_info.content_type)
