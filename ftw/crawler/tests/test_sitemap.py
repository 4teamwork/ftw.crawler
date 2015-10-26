from ftw.crawler.configuration import Site
from ftw.crawler.exceptions import FtwCrawlerException
from ftw.crawler.sitemap import Sitemap
from ftw.crawler.sitemap import SitemapFetcher
from ftw.crawler.testing import CrawlerTestCase
from ftw.crawler.tests.helpers import get_asset
from ftw.crawler.tests.helpers import MockResponse
from mock import patch


SITEMAP = get_asset('sitemap.xml')
SITEMAP_GZ = get_asset('sitemap.xml.gz')
SITEMAP_REQ_ONLY = get_asset('sitemap_req_only.xml')


class TestSitemapFetcher(CrawlerTestCase):

    def setUp(self):
        CrawlerTestCase.setUp(self)
        self.site = Site('http://example.org/')
        self.response = MockResponse(SITEMAP)

    @patch('requests.get')
    def test_finds_and_fetches_sitemap(self, request):
        request.return_value = self.response
        sm_fetcher = SitemapFetcher(self.site)
        sitemap = sm_fetcher.fetch()
        self.assertEquals(2, len(sitemap.url_infos))

    @patch('requests.get')
    def test_falls_back_to_gzipped_sitemap(self, request):
        responses = {
            'http://example.org/sitemap.xml': MockResponse(
                status_code=404),
            'http://example.org/sitemap.xml.gz': MockResponse(
                status_code=200,
                content=SITEMAP_GZ,
                headers={'Content-Type': 'application/x-gzip'})}

        request.side_effect = lambda url: responses[url]
        sm_fetcher = SitemapFetcher(self.site)
        sitemap = sm_fetcher.fetch()

        self.assertEquals(2, len(sitemap.url_infos))

    @patch('requests.get')
    def test_raises_if_no_sitemap_found(self, request):
        not_found = MockResponse(status_code=404)
        request.return_value = not_found

        sm_fetcher = SitemapFetcher(self.site)
        with self.assertRaises(FtwCrawlerException):
            sm_fetcher.fetch()

    @patch('requests.get')
    def test_decompresses_gzipped_sitemap(self, request):
        not_found = MockResponse(status_code=404)
        found_gz = MockResponse(status_code=200, content=SITEMAP_GZ,
                                headers={'Content-Type': 'application/x-gzip'})
        responses = {'http://example.org/sitemap.xml': not_found,
                     'http://example.org/sitemap.xml.gz': found_gz}

        request.side_effect = lambda url: responses[url]

        sm_fetcher = SitemapFetcher(self.site)
        sitemap = sm_fetcher.fetch()

        self.assertIn('http://example.org/foo', sitemap)
        self.assertIn('http://example.org/bar', sitemap)
        self.assertEquals(2, len(sitemap.url_infos))

    @patch('requests.get')
    def test_doesnt_choke_on_charset_in_content_type(self, request):
        request.return_value = MockResponse(
            content=SITEMAP,
            headers={'Content-Type': 'text/html; charset=utf-8'})
        sm_fetcher = SitemapFetcher(self.site)
        sitemap = sm_fetcher.fetch()
        self.assertEquals(2, len(sitemap.url_infos))


class TestSitemap(CrawlerTestCase):

    def setUp(self):
        self.site = Site('http://example.org/')

    def test_parses_sitemap(self):
        sitemap = Sitemap(SITEMAP, self.site)

        self.assertEqual([
            {'loc': 'http://example.org/foo',
             'changefreq': 'daily',
             'lastmod': '2014-12-31',
             'priority': '1.0'},
            {'loc': 'http://example.org/bar',
             'target': 'http://example.org/target-bar',
             'changefreq': 'daily',
             'lastmod': '2005-01-01',
             'priority': '1.0'}],
            sitemap.url_infos)

    def test_deals_with_missing_elements(self):
        sitemap = Sitemap(SITEMAP_REQ_ONLY, self.site)

        self.assertEqual([
            {'loc': 'http://example.org/foo'},
            {'loc': 'http://example.org/bar'}],
            sitemap.url_infos)

    def test_keeps_reference_to_site(self):
        sitemap = Sitemap(SITEMAP_REQ_ONLY, self.site)

        self.assertEqual(self.site, sitemap.site)

    def test_supports_testing_for_membership(self):
        sitemap = Sitemap(SITEMAP_REQ_ONLY, self.site)

        self.assertIn('http://example.org/foo', sitemap)
        self.assertNotIn('http://example.org/not_contained', sitemap)

    def test_testing_for_membership_is_case_insensitive(self):
        sitemap = Sitemap(SITEMAP_REQ_ONLY, self.site)

        self.assertIn('http://example.org/foo', sitemap)
        self.assertIn('HTTP://EXAMPLE.ORG/FOO', sitemap)
