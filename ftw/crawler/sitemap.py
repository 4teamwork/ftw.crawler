from ftw.crawler.exceptions import NoSitemapFound
from ftw.crawler.utils import gunzip
from ftw.crawler.utils import is_gzipped
from ftw.crawler.xml_utils import remove_namespaces
from lxml import etree
from urlparse import urljoin
import io
import logging
import requests


SITEMAP_NAMES = ('sitemap.xml', 'sitemap.xml.gz')
SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
PROPERTIES = ('loc', 'lastmod', 'changefreq', 'priority', 'target')

log = logging.getLogger(__name__)


class SitemapFetcher(object):
    """Looks for a sitemap on a given site, then downloads it and returns a
    ``Sitemap`` object.
    """
    def __init__(self, site):
        self.site = site

    def fetch(self):
        """Discovers and downloads the sitemap for the given site, returning
        a ``Sitemap`` object.
        """
        log.info(u'Fetching sitemap for {}'.format(self.site.url))
        for sm_name in SITEMAP_NAMES:
            url = urljoin(self.site.url, sm_name)
            response = requests.get(url)

            if response.status_code == 200:
                sitemap_xml = response.content

                if is_gzipped(response):
                    sitemap_xml = gunzip(sitemap_xml)

                return Sitemap(sitemap_xml, self.site, url)

        raise NoSitemapFound(
            "No sitemap found for {}!".format(self.site.url))


class Sitemap(object):
    """Represents a single sitemap on a site.
    """

    def __init__(self, sitemap_xml, site, url=None):
        self.site = site
        self.url = url
        self.tree = self._parse_sitemap_xml(sitemap_xml)
        self._url_infos = None

    @property
    def url_infos(self):
        """Memoized property that returns a list of dictionaries containing
        the parsed <urlinfo>s.
        """
        if self._url_infos is None:
            self._url_infos = list(self._get_url_infos())
        return self._url_infos

    def __contains__(self, url):
        """Tests whether an URL is listed in this sitemap (case-insensitive).
        """
        url_infos = self.url_infos
        return url.lower() in (ui['loc'].lower() for ui in url_infos)

    def _parse_sitemap_xml(self, sitemap_xml):
        tree = etree.parse(io.BytesIO(sitemap_xml))
        tree = remove_namespaces(tree)
        return tree

    def _get_url_infos(self):
        url_nodes = self.tree.xpath('/urlset/url')
        for node in url_nodes:
            url_info = {}
            for name in PROPERTIES:
                results = node.xpath("{}/text()".format(name))
                if results:
                    url_info[name] = results[0]
            yield url_info
