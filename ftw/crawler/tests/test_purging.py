from argparse import Namespace
from copy import deepcopy
from ftw.crawler.configuration import get_config
from ftw.crawler.purging import purge_removed_docs_from_index
from ftw.crawler.sitemap import VirtualSitemapIndex
from ftw.crawler.testing import SitemapTestCase
from ftw.crawler.testing import SolrTestCase
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
            {'UID': '1', 'url': 'http://www.pctipp.ch/download'},
            {'UID': '2', 'url': 'http://www.pctipp.ch/about'},
        ]
        pctipp = self.config.get_site('http://www.pctipp.ch/')

        sitemap = self.create_sitemap(
            urls=['http://www.pctipp.ch/download'],
            site=pctipp)

        sitemap_index = VirtualSitemapIndex(pctipp, sitemaps=[sitemap])
        purge_removed_docs_from_index(self.config, sitemap_index, indexed_docs)

        delete.assert_called_with(u'2')
        self.assertEqual(1, delete.call_count)

    @patch('ftw.crawler.solr.SolrConnector.delete')
    def test_doesnt_touch_any_docs_not_starting_with_site_urls(self, delete):
        indexed_docs = [
            {'UID': '1', 'url': 'http://www.pctipp.ch/download'},
            {'UID': '2', 'url': 'http://www.pctipp.ch/about'},
            {'UID': '3', 'url': 'http://some.com/other/url'},
        ]
        pctipp = self.config.get_site('http://www.pctipp.ch/')

        sitemap = self.create_sitemap(
            urls=['http://www.pctipp.ch/download',
                  'http://www.pctipp.ch/about'],
            site=pctipp)

        sitemap_index = VirtualSitemapIndex(pctipp, sitemaps=[sitemap])
        purge_removed_docs_from_index(self.config, sitemap_index, indexed_docs)

        self.assertEquals(0, delete.call_count)
