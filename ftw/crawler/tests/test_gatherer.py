from ftw.crawler.exceptions import FtwCrawlerException
from ftw.crawler.gatherer import URLGatherer
from ftw.crawler.tests.helpers import get_asset
from ftw.crawler.tests.helpers import MockResponse
from mock import patch
from unittest2 import TestCase


SITEMAP = get_asset('sitemap.xml')
SITEMAP_GZ = get_asset('sitemap.xml.gz')


class TestGatherer(TestCase):

    def setUp(self):
        self.response = MockResponse(SITEMAP)

    @patch('requests.get')
    def test_finds_and_fetches_sitemap(self, request):
        request.return_value = self.response
        gatherer = URLGatherer('http://example.org/')
        sitemap_xml = gatherer.fetch_sitemap()
        self.assertEquals(SITEMAP, sitemap_xml)

    @patch('requests.get')
    def test_falls_back_to_gzipped_sitemap(self, request):
        not_found = MockResponse(status_code=404)
        found = MockResponse(status_code=200, content='MARKER')
        responses = {'http://example.org/sitemap.xml': not_found,
                     'http://example.org/sitemap.xml.gz': found}

        request.side_effect = lambda url: responses[url]
        gatherer = URLGatherer('http://example.org/')
        sitemap_xml = gatherer.fetch_sitemap()

        self.assertEquals('MARKER', sitemap_xml)

    @patch('requests.get')
    def test_raises_if_no_sitemap_found(self, request):
        not_found = MockResponse(status_code=404)
        request.return_value = not_found

        gatherer = URLGatherer('http://example.org/')
        with self.assertRaises(FtwCrawlerException):
            gatherer.fetch_sitemap()

    @patch('requests.get')
    def test_decompresses_gzipped_sitemap(self, request):
        not_found = MockResponse(status_code=404)
        found_gz = MockResponse(status_code=200, content=SITEMAP_GZ,
                                headers={'Content-Type': 'application/x-gzip'})
        responses = {'http://example.org/sitemap.xml': not_found,
                     'http://example.org/sitemap.xml.gz': found_gz}

        request.side_effect = lambda url: responses[url]
        gatherer = URLGatherer('http://example.org/')
        sitemap_xml = gatherer.fetch_sitemap()

        self.assertEquals(
            SITEMAP, sitemap_xml,
            "SITEMAP_GZ should have been decompressed to SITEMAP")
