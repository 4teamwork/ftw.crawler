from ftw.crawler.exceptions import FetchingError
from ftw.crawler.fetcher import ResourceFetcher
from ftw.crawler.tests.helpers import MockFile
from ftw.crawler.tests.helpers import MockResponse
from mock import patch
from unittest2 import TestCase


class TestResourceFetcher(TestCase):

    @patch('requests.get')
    def test_fetches_and_saves_resource(self, request):
        request.return_value = MockResponse(
            content='MARKER', headers={'Content-Type': 'text/html'})
        resource_file = MockFile(name='/var/tmp/foo')

        url_info = {'loc': 'http://example.org/'}
        fetcher = ResourceFetcher(url_info, resource_file)
        resource_fn, content_type = fetcher.fetch()

        self.assertEquals('/var/tmp/foo', resource_fn)
        self.assertEquals('MARKER', resource_file.read())
        self.assertEquals('text/html', content_type)

    @patch('requests.get')
    def test_raises_if_not_200_ok(self, request):
        request.return_value = MockResponse(status_code=404)
        resource_file = MockFile()

        url_info = {'loc': 'http://example.org/'}
        fetcher = ResourceFetcher(url_info, resource_file)
        with self.assertRaises(FetchingError):
            fetcher.fetch()

    @patch('requests.get')
    def test_doesnt_choke_on_charset_in_content_type(self, request):
        request.return_value = MockResponse(
            content='', headers={'Content-Type': 'text/html; charset=utf-8'})
        resource_file = MockFile()

        url_info = {'loc': 'http://example.org/'}
        fetcher = ResourceFetcher(url_info, resource_file)
        _, content_type = fetcher.fetch()

        self.assertEquals('text/html', content_type)
