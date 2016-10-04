from ftw.crawler.configuration import Site
from ftw.crawler.exceptions import NoSitemapFound
from ftw.crawler.sitemap import Sitemap
from ftw.crawler.sitemap import SitemapFetcher
from ftw.crawler.sitemap import SitemapIndex
from ftw.crawler.sitemap import SitemapIndexFetcher
from ftw.crawler.sitemap import VirtualSitemapIndex
from ftw.crawler.testing import SitemapTestCase
from ftw.crawler.tests.helpers import get_asset
from ftw.crawler.tests.helpers import MockResponse
from mock import patch


XHTML_DOC = get_asset('xhtml_doc.html')
SITEMAP = get_asset('sitemap.xml')
SITEMAP_GZ = get_asset('sitemap.xml.gz')
SITEMAP_REQ_ONLY = get_asset('sitemap_req_only.xml')

SITEMAP_INDEX = get_asset('sitemap_index.xml')
SITEMAP_INDEX_GZ = get_asset('sitemap_index.xml.gz')
SITEMAP_INDEX_REQ_ONLY = get_asset('sitemap_index_req_only.xml')


class TestSitemapFetcher(SitemapTestCase):

    def setUp(self):
        SitemapTestCase.setUp(self)
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
            'http://example.org/': MockResponse(status_code=404),
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
    def test_fetches_sitemap_from_url_without_discovery(self, request):
        responses = {
            'http://example.org/sitemap.xml': MockResponse(
                status_code=404),
            'http://example.org/foo/sitemap.xml': MockResponse(
                status_code=200,
                content=SITEMAP),
        }
        request.side_effect = lambda url: responses[url]

        sm_fetcher = SitemapFetcher(self.site)
        sitemap = sm_fetcher.fetch('http://example.org/foo/sitemap.xml')
        self.assertEquals(2, len(sitemap.url_infos))

    @patch('requests.get')
    def test_fetches_gzipped_sitemap_from_url_without_discovery(self, request):
        responses = {
            'http://example.org/sitemap.xml': MockResponse(
                status_code=404),
            'http://example.org/foo/sitemap.xml.gz': MockResponse(
                status_code=200,
                content=SITEMAP_GZ,
                headers={'Content-Type': 'application/x-gzip'})}
        request.side_effect = lambda url: responses[url]

        sm_fetcher = SitemapFetcher(self.site)
        sitemap = sm_fetcher.fetch('http://example.org/foo/sitemap.xml.gz')
        self.assertEquals(2, len(sitemap.url_infos))

    @patch('requests.get')
    def test_raises_if_no_sitemap_found(self, request):
        not_found = MockResponse(status_code=404)
        request.return_value = not_found

        sm_fetcher = SitemapFetcher(self.site)
        with self.assertRaises(NoSitemapFound):
            sm_fetcher.fetch()

    @patch('requests.get')
    def test_decompresses_gzipped_sitemap(self, request):
        not_found = MockResponse(status_code=404)
        html = MockResponse(status_code=200, content=XHTML_DOC)
        found_gz = MockResponse(status_code=200, content=SITEMAP_GZ,
                                headers={'Content-Type': 'application/x-gzip'})
        responses = {'http://example.org/': html,
                     'http://example.org/sitemap.xml': not_found,
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

    @patch('requests.get')
    def test_supports_absolute_sitemap_urls(self, request):
        responses = {
            'http://example.org/foo/bar/seitenkarte': MockResponse(
                status_code=200,
                content=SITEMAP),
        }
        request.side_effect = lambda url: responses[url]

        site = Site('http://example.org/foo/bar/seitenkarte')
        sm_fetcher = SitemapFetcher(site)
        sitemap = sm_fetcher.fetch()
        self.assertEquals(2, len(sitemap.url_infos))


class TestSitemap(SitemapTestCase):

    def setUp(self):
        super(SitemapTestCase, self).setUp()
        self.site = Site('http://example.org/')

    def test_parses_sitemap(self):
        sitemap = Sitemap(self.site, SITEMAP)

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
        sitemap = Sitemap(self.site, SITEMAP_REQ_ONLY)

        self.assertEqual([
            {'loc': 'http://example.org/foo'},
            {'loc': 'http://example.org/bar'}],
            sitemap.url_infos)

    def test_keeps_reference_to_site(self):
        sitemap = Sitemap(self.site, SITEMAP_REQ_ONLY)

        self.assertEqual(self.site, sitemap.site)

    def test_supports_testing_for_membership(self):
        sitemap = Sitemap(self.site, SITEMAP_REQ_ONLY)

        self.assertIn('http://example.org/foo', sitemap)
        self.assertNotIn('http://example.org/not_contained', sitemap)

    def test_testing_for_membership_is_case_insensitive(self):
        sitemap = Sitemap(self.site, SITEMAP_REQ_ONLY)

        self.assertIn('http://example.org/foo', sitemap)
        self.assertIn('HTTP://EXAMPLE.ORG/FOO', sitemap)


class TestSitemapIndex(SitemapTestCase):

    def setUp(self):
        super(SitemapTestCase, self).setUp()
        self.site = Site('http://example.org/')

    def test_parses_sitemap_index(self):
        sitemap_index = SitemapIndex(self.site, SITEMAP_INDEX)

        self.assertEqual([
            {'loc': 'http://example.org/foo-sitemap.xml',
             'lastmod': '2015-10-23T14:00:05+02:00'},
            {'loc': 'http://example.org/bar-sitemap.xml',
             'lastmod': '2015-10-23T16:00:05+02:00'}],
            sitemap_index.sitemap_infos)

    def test_deals_with_missing_elements(self):
        sitemap_index = SitemapIndex(self.site, SITEMAP_INDEX_REQ_ONLY)

        self.assertEqual([
            {'loc': 'http://example.org/foo-sitemap.xml'},
            {'loc': 'http://example.org/bar-sitemap.xml'}],
            sitemap_index.sitemap_infos)

    def test_keeps_reference_to_site(self):
        sitemap_index = SitemapIndex(self.site, SITEMAP_INDEX)

        self.assertEqual(self.site, sitemap_index.site)

    def test_supports_testing_for_membership(self):
        sitemap_foo = self.create_sitemap(urls=['http://example.org/foo'])
        sitemap_bar = self.create_sitemap(urls=['http://example.org/bar'])
        sitemap_index = VirtualSitemapIndex(
            self.site, sitemaps=[sitemap_foo, sitemap_bar])

        self.assertIn('http://example.org/foo', sitemap_index)
        self.assertIn('http://example.org/bar', sitemap_index)
        self.assertNotIn('http://example.org/not_contained', sitemap_index)

    def test_testing_for_membership_is_case_insensitive(self):
        sitemap = Sitemap(self.site, SITEMAP)
        sitemap_index = VirtualSitemapIndex(self.site, sitemaps=[sitemap])

        self.assertIn('http://example.org/foo', sitemap_index)
        self.assertIn('HTTP://EXAMPLE.ORG/FOO', sitemap_index)


class TestSitemapIndexFetcher(SitemapTestCase):

    def setUp(self):
        SitemapTestCase.setUp(self)
        self.site = Site('http://example.org/')
        self.response = MockResponse(SITEMAP_INDEX)

    @patch('requests.get')
    def test_finds_and_fetches_sitemap_index(self, request):
        request.return_value = self.response
        sm_idx_fetcher = SitemapIndexFetcher(self.site)
        sitemap_index = sm_idx_fetcher.fetch()
        self.assertEquals(2, len(sitemap_index.sitemap_infos))

    @patch('requests.get')
    def test_falls_back_to_gzipped_sitemap_index(self, request):
        responses = {
            'http://example.org/': MockResponse(status_code=404),
            'http://example.org/sitemap_index.xml': MockResponse(
                status_code=404),
            'http://example.org/sitemap_index.xml.gz': MockResponse(
                status_code=200,
                content=SITEMAP_INDEX_GZ,
                headers={'Content-Type': 'application/x-gzip'})}

        request.side_effect = lambda url, **kwargs: responses[url]
        sm_idx_fetcher = SitemapIndexFetcher(self.site)
        sitemap_index = sm_idx_fetcher.fetch()

        self.assertEquals(2, len(sitemap_index.sitemap_infos))

    @patch('requests.get')
    def test_returns_virtual_index_if_no_sitemap_index_found(self, request):
        not_found = MockResponse(status_code=404)
        responses = {
            'http://example.org/sitemap_index.xml': not_found,
            'http://example.org/sitemap_index.xml.gz': not_found,
            'http://example.org/sitemap.xml': MockResponse(
                status_code=200,
                content=SITEMAP),
            'http://example.org/': MockResponse(
                status_code=200,
                content=XHTML_DOC),
        }
        request.side_effect = lambda url, **kwargs: responses[url]

        sm_idx_fetcher = SitemapIndexFetcher(self.site)
        sitemap_index = sm_idx_fetcher.fetch()

        self.assertIsInstance(sitemap_index, VirtualSitemapIndex)
        self.assertIn('http://example.org/foo', sitemap_index)

    @patch('requests.get')
    def test_decompresses_gzipped_sitemap_index(self, request):
        not_found = MockResponse(status_code=404)
        found_gz = MockResponse(status_code=200, content=SITEMAP_INDEX_GZ,
                                headers={'Content-Type': 'application/x-gzip'})
        responses = {'http://example.org/': MockResponse(status_code=404),
                     'http://example.org/sitemap_index.xml': not_found,
                     'http://example.org/sitemap_index.xml.gz': found_gz}

        request.side_effect = lambda url, **kwargs: responses[url]

        sm_idx_fetcher = SitemapIndexFetcher(self.site)
        sitemap_index = sm_idx_fetcher.fetch()

        self.assertEquals(2, len(sitemap_index.sitemap_infos))

    @patch('requests.get')
    def test_doesnt_choke_on_charset_in_content_type(self, request):
        request.return_value = MockResponse(
            content=SITEMAP_INDEX,
            headers={'Content-Type': 'text/html; charset=utf-8'})
        sm_idx_fetcher = SitemapIndexFetcher(self.site)
        sitemap_index = sm_idx_fetcher.fetch()
        self.assertEquals(2, len(sitemap_index.sitemap_infos))

    @patch('requests.get')
    def test_supports_absolute_sitemap_index_urls(self, request):
        responses = {
            'http://example.org/foo/bar/seitenverzeichnisse': MockResponse(
                status_code=200,
                content=SITEMAP_INDEX),
        }
        request.side_effect = lambda url, **kwargs: responses[url]

        site = Site('http://example.org/foo/bar/seitenverzeichnisse')
        sm_idx_fetcher = SitemapIndexFetcher(site)
        sitemap_index = sm_idx_fetcher.fetch()
        self.assertEquals(2, len(sitemap_index.sitemap_infos))
