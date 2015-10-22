from argparse import Namespace
from copy import deepcopy
from ftw.crawler.configuration import get_config
from ftw.crawler.purging import purge_removed_docs_from_index
from ftw.crawler.testing import SitemapTestCase
from ftw.crawler.testing import SolrTestCase
from mock import call
from mock import patch
from pkg_resources import resource_filename


BASIC_CONFIG = resource_filename('ftw.crawler.tests.assets', 'basic_config.py')


class TestPurging(SolrTestCase, SitemapTestCase):

    def setUp(self):
        SolrTestCase.setUp(self)
        SitemapTestCase.setUp(self)
        args = Namespace(tika=None, solr=None)
        args.config = BASIC_CONFIG
        self.config = deepcopy(get_config(args))
        self.config.url_field = 'url'

    @patch('ftw.crawler.solr.SolrConnector.delete')
    def test_purges_doc_removed_from_sitemap(self, delete):
        indexed_docs = [
            {'UID': '1', 'url': 'https://www.dropbox.com/download'},
            {'UID': '2', 'url': 'https://www.dropbox.com/about'},
        ]
        dropbox = self.config.sites[1]

        sitemap = self.create_sitemap(
            urls=['https://www.dropbox.com/download'],
            site=dropbox)

        purge_removed_docs_from_index(
            self.config, [sitemap], indexed_docs, dropbox)
        delete.assert_called_with(u'2')
        self.assertEqual(1, delete.call_count)

    @patch('ftw.crawler.solr.SolrConnector.delete')
    def test_doesnt_touch_any_docs_not_starting_with_site_urls(self, delete):
        indexed_docs = [
            {'UID': '1', 'url': 'https://www.dropbox.com/download'},
            {'UID': '2', 'url': 'https://www.dropbox.com/about'},
            {'UID': '3', 'url': 'https://some.com/other/url'},
        ]
        dropbox = self.config.sites[1]

        sitemap = self.create_sitemap(
            urls=['https://www.dropbox.com/download',
                  'https://www.dropbox.com/about'],
            site=dropbox)

        purge_removed_docs_from_index(
            self.config, [sitemap], indexed_docs, dropbox)
        self.assertEquals(0, delete.call_count)

    @patch('ftw.crawler.solr.SolrConnector.delete')
    def test_handles_multiple_sitemaps(self, delete):
        indexed_docs = [
            {'UID': '1', 'url': 'https://www.dropbox.com/about/team'},
            {'UID': '2', 'url': 'https://www.dropbox.com/about/partners'},
            {'UID': '3', 'url': 'https://www.dropbox.com/help/faq'},
            {'UID': '4', 'url': 'https://www.dropbox.com/help/forum'},
        ]
        dropbox = self.config.sites[1]

        sitemap_about = self.create_sitemap(
            urls=['https://www.dropbox.com/about/team'],
            site=dropbox)

        sitemap_help = self.create_sitemap(
            urls=['https://www.dropbox.com/help/faq'],
            site=dropbox)

        purge_removed_docs_from_index(
            self.config, [sitemap_about, sitemap_help], indexed_docs, dropbox)

        # Should ONLY remove docs that have disappeared from sitemaps
        self.assertEqual(delete.mock_calls, [call(u'2'), call(u'4')])
