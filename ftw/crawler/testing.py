from argparse import Namespace
from ftw.crawler.fetcher import ResourceFetcher
from ftw.crawler.resource import ResourceInfo
from ftw.crawler.sitemap import Sitemap
from ftw.crawler.tests.helpers import get_asset
from ftw.crawler.tests.helpers import MockResponse
from lxml import etree
from unittest2 import TestCase
import calendar
import json
import logging
import requests


def timestamp(dt):
    return calendar.timegm(dt.utctimetuple())


class CrawlerTestCase(TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)


class XMLTestCase(CrawlerTestCase):

    def tostring(self, xml):
        return etree.tostring(xml, xml_declaration=True,
                              encoding='utf-8', pretty_print=True)

    def tree_from_str(self, xml):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.XML(xml.strip(), parser=parser)
        return root.getroottree()

    def assertXMLEquals(self, expected, actual):
        """Assert two strings of XML are equal by normalizing
        whitespace outside text nodes.
        """
        actual_xml = self.tostring(self.tree_from_str(actual))
        expected_xml = self.tostring(self.tree_from_str(expected))
        return self.assertEquals(expected_xml, actual_xml)


class DatetimeTestCase(CrawlerTestCase):

    def assertDatetimesAlmostEqual(self, expected, actual, delta=2):
        expected_ts = timestamp(expected)
        actual_ts = timestamp(actual)
        msg = "datetimes {} and {} aren't within {} seconds.".format(
            expected, actual, delta)
        return self.assertAlmostEqual(expected_ts, actual_ts,
                                      delta=delta, msg=msg)


class FetcherTestCase(CrawlerTestCase):

    def _create_fetcher(self, resource_info=None, session=None, tempdir=None,
                        options=None):
        if resource_info is None:
            resource_info = ResourceInfo()

        if session is None:
            session = requests.Session()

        if options is None:
            options = Namespace(force=False)

        return ResourceFetcher(
            resource_info=resource_info, session=session, tempdir=tempdir,
            options=options)


SITEMAP = get_asset('sitemap.xml')


class SitemapTestCase(CrawlerTestCase):

    def create_sitemap(self, urls=None, site=None, sitemap_url=None):
        sitemap = Sitemap(site, SITEMAP, url=sitemap_url)
        del sitemap.tree
        url_infos = [{'loc': url} for url in urls]
        sitemap._url_infos = url_infos
        return sitemap


SOLR_RESULTS_TEMPLATE = """\
{
  "responseHeader": {
    "status": 0,
    "QTime": 0,
    "params": {
    }
  },
  "response": {
    "numFound": %s,
    "start": 0,
    "docs": %s
  }
}
"""


class SolrTestCase(CrawlerTestCase):

    def create_solr_response(self, status=200, content=None, headers=None):
        if content is None:
            content = '{"responseHeader":{"status":%s,"QTime":10}}' % status

        if headers is None:
            headers = {'content-type': 'application/json; charset=UTF-8'}

        response = MockResponse(
            status_code=status,
            content=content,
            headers={'content-type': 'application/json; charset=UTF-8'})
        return response

    def create_solr_results(self, docs):
        docs = json.dumps(docs)
        content = SOLR_RESULTS_TEMPLATE % (len(docs), docs)
        response = self.create_solr_response(content=content)
        return response
