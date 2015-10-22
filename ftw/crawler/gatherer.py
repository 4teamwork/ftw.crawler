from ftw.crawler.exceptions import FtwCrawlerException
from ftw.crawler.utils import get_content_type
from urlparse import urljoin
from urlparse import urlsplit
import gzip
import io
import logging
import requests


log = logging.getLogger(__name__)

SITEMAP_NAMES = ('sitemap.xml', 'sitemap.xml.gz')


class URLGatherer(object):

    def __init__(self, site_url):
        self.site_url = site_url

    def fetch_sitemap(self):
        log.info(u'Fetching sitemap for {}'.format(self.site_url))
        for sm_name in SITEMAP_NAMES:
            url = urljoin(self.site_url, sm_name)
            response = requests.get(url)

            if response.status_code == 200:
                if self.is_gzipped(response):
                    return url, self.gunzip(response.content)
                return url, response.content

        raise FtwCrawlerException(
            "No sitemap could be found for {}!".format(self.site_url))

    def is_gzipped(self, response):
        """Determine if a response's content is gzipped.

        This only considers the Content-Type header and the filename, NOT
        HTTP compression indicated by the Content-Encoding header, which is
        handled transparently by the `requests` module.
        """
        content_type = get_content_type(response.headers.get('Content-Type'))
        path = urlsplit(response.request.url).path
        return content_type == 'application/x-gzip' or path.endswith('.gz')

    def gunzip(self, content):
        """Decompress a gzipped bytestring.
        """
        f = gzip.GzipFile(mode='rb', fileobj=io.BytesIO(content))
        return f.read()
