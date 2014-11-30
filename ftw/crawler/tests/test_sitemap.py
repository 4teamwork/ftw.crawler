from ftw.crawler.configuration import Site
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

    def test_keeps_reference_to_site(self):
        site = Site('http://example.org')
        sitemap = SitemapParser(SITEMAP_REQ_ONLY, site=site)
        self.assertEqual(site, sitemap.site)

    def test_supports_testing_for_membership(self):
        sitemap = SitemapParser(SITEMAP_REQ_ONLY)
        self.assertIn('http://example.org/foo', sitemap)
        self.assertNotIn('http://example.org/not_contained', sitemap)

    def test_testing_for_membership_is_case_insensitive(self):
        sitemap = SitemapParser(SITEMAP_REQ_ONLY)
        self.assertIn('http://example.org/foo', sitemap)
        self.assertIn('HTTP://EXAMPLE.ORG/FOO', sitemap)
