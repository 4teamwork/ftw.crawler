from ftw.crawler.sitemap import SitemapParser
from ftw.crawler.tests.helpers import get_asset
from unittest2 import TestCase


SITEMAP = get_asset('sitemap.xml')
SITEMAP_REQ_ONLY = get_asset('sitemap_req_only.xml')


class TestSitemapParser(TestCase):

    def test_parses_sitemap(self):
        parser = SitemapParser(SITEMAP)
        parser.parse()
        url_infos = parser.get_urls()

        self.assertEqual([
            {'loc': 'http://example.org/foo',
             'changefreq': 'daily',
             'lastmod': '2014-12-31',
             'priority': '1.0'},
            {'loc': 'http://example.org/bar',
             'changefreq': 'daily',
             'lastmod': '2005-01-01',
             'priority': '1.0'}],
            list(url_infos))

    def test_deals_with_missing_elements(self):
        sitemap = SitemapParser(SITEMAP_REQ_ONLY)
        url_infos = sitemap.get_urls()

        self.assertEqual([
            {'loc': 'http://example.org/foo'},
            {'loc': 'http://example.org/bar'}],
            list(url_infos))
