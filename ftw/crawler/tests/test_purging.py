from argparse import Namespace
from copy import deepcopy
from ftw.crawler.configuration import get_config
from ftw.crawler.purging import purge_removed_docs_from_index
from ftw.crawler.solr import SolrConnector
from ftw.crawler.testing import SitemapTestCase
from ftw.crawler.testing import SolrTestCase
from mock import patch
from pkg_resources import resource_filename


BASIC_CONFIG = resource_filename('ftw.crawler.tests.assets', 'basic_config.py')


class TestPurging(SolrTestCase, SitemapTestCase):

    def setUp(self):
        args = Namespace()
        args.config = BASIC_CONFIG
        self.config = deepcopy(get_config(args))
        self.config.url_field = 'url'

        self.solr = SolrConnector(self.config.solr)

        self.docs = [
            {'UID': '1', 'url': 'http://www.sitemapxml.co.uk/index.php'},
            {'UID': '2', 'url': 'https://www.dropbox.com/download'},
            {'UID': '3', 'url': 'https://www.dropbox.com/about'},
        ]
        self.response_search_results = self.create_solr_results(self.docs)

    @patch('ftw.crawler.solr.SolrConnector.delete')
    @patch('requests.get')
    def test_purges_doc_removed_from_sitemap(self, request, delete):
        request.return_value = self.response_search_results
        sitemaps_co_uk = self.config.sites[0]
        dropbox = self.config.sites[1]

        sitemaps = [
            self.create_sitemap(
                urls=['http://www.sitemapxml.co.uk/index.php'],
                site=sitemaps_co_uk),
            self.create_sitemap(
                urls=['https://www.dropbox.com/download'],
                site=dropbox),
        ]
        purge_removed_docs_from_index(self.config, self.solr, sitemaps)
        delete.assertCalledWith(u'3')

    @patch('ftw.crawler.solr.SolrConnector.delete')
    @patch('requests.get')
    def test_doesnt_touch_any_docs_not_starting_with_site_urls(
            self, request, delete):
        docs = self.docs[:]
        docs.append({'UID': '4', 'url': 'https://some.com/other/url'})
        request.return_value = self.response_search_results
        sitemaps_co_uk = self.config.sites[0]
        dropbox = self.config.sites[1]

        sitemaps = [
            self.create_sitemap(
                urls=['http://www.sitemapxml.co.uk/index.php'],
                site=sitemaps_co_uk),
            self.create_sitemap(
                urls=['https://www.dropbox.com/download',
                      'https://www.dropbox.com/about'],
                site=dropbox),
        ]
        purge_removed_docs_from_index(self.config, self.solr, sitemaps)
        self.assertEquals(0, delete.call_count)
