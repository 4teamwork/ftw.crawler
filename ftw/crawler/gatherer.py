from urlparse import urljoin
from ftw.crawler.exceptions import FtwCrawlerException
import logging
import requests


log = logging.getLogger(__name__)

SITEMAP_NAMES = ('sitemap.xml', 'sitemap.xml.gz')


class URLGatherer(object):

    def __init__(self, site_url):
        self.site_url = site_url

    def fetch_sitemap(self):
        log.info('Fetching sitemap for {}'.format(self.site_url))
        for sm_name in SITEMAP_NAMES:
            url = urljoin(self.site_url, sm_name)
            response = requests.get(url)
            if response.status_code == 200:
                return response.content
        raise FtwCrawlerException(
            "No sitemap could be found for {}!".format(self.site_url))
