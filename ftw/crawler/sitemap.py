from ftw.crawler.exceptions import NoSitemapFound
from ftw.crawler.utils import gunzip
from ftw.crawler.utils import is_gzipped
from ftw.crawler.xml_utils import remove_namespaces
from lxml import etree
from urlparse import urljoin
import io
import logging
import requests


SITEMAP_INDEX_NAMES = ('', 'sitemap_index.xml', 'sitemap_index.xml.gz')
SITEMAP_NAMES = ('', 'sitemap.xml', 'sitemap.xml.gz')
SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
PROPERTIES = ('loc', 'lastmod', 'changefreq', 'priority', 'target')

log = logging.getLogger(__name__)


class SitemapIndexFetcher(object):
    """Looks for a sitemap index on a given site, then downloads it and
    returns a ``SitemapIndex`` object.
    """
    def __init__(self, site):
        self.site = site

    def fetch(self):
        """Discovers and downloads the sitemap index for the given site,
        returning a ``SitemapIndex`` object.
        """
        log.info(u'Fetching sitemap index for {}'.format(self.site.url))
        for sm_idx_name in SITEMAP_INDEX_NAMES:
            url = urljoin(self.site.url, sm_idx_name)
            response = requests.get(url, allow_redirects=False)

            if response.status_code == 200:
                sitemap_idx_xml = response.content

                if is_gzipped(response):
                    sitemap_idx_xml = gunzip(sitemap_idx_xml)

                index = SitemapIndex(self.site, sitemap_idx_xml, url)
                if index.is_sitemap_index():
                    return index

        # No sitemap index found - build a virtual one with a single sitemap
        sitemap = SitemapFetcher(self.site).fetch()
        return VirtualSitemapIndex(self.site, sitemaps=[sitemap])


class SitemapIndex(object):
    """Represents a sitemap index on a site, containing one or more sitemaps.
    """

    def __init__(self, site, sitemap_idx_xml, url=None):
        self.site = site
        self.url = url
        self.tree = self._parse_sitemap_idx_xml(sitemap_idx_xml)

        self._sitemap_infos = None
        self._sitemaps = None

    def is_sitemap_index(self):
        return len(self.tree.xpath('//sitemapindex')) > 0

    @property
    def sitemaps(self):
        """Memoized property that returns a list of ``Sitemap``s contained in
        this sitemap index.
        """
        if self._sitemaps is None:
            self._sitemaps = list(self._fetch_sitemaps())
        return self._sitemaps

    def __contains__(self, url):
        """Tests whether an URL is listed in any of the sitemaps contained in
        this sitemap index (case-insensitive).
        """
        return any(url in sm for sm in self.sitemaps)

    @property
    def sitemap_infos(self):
        """Memoized property that returns a list of dictionaries containing
        the parsed <sitemap> entries.
        """
        if self._sitemap_infos is None:
            self._sitemap_infos = list(self._get_sitemap_infos())
        return self._sitemap_infos

    def _fetch_sitemaps(self):
        for sitemap_info in self.sitemap_infos:
            url = sitemap_info['loc']
            sitemap = SitemapFetcher(self.site).fetch(url)
            yield sitemap

    def _parse_sitemap_idx_xml(self, sitemap_idx_xml):
        tree = etree.parse(io.BytesIO(sitemap_idx_xml))
        tree = remove_namespaces(tree)
        return tree

    def _get_sitemap_infos(self):
        sitemap_nodes = self.tree.xpath('/sitemapindex/sitemap')
        for node in sitemap_nodes:
            sitemap_info = {}
            for name in PROPERTIES:
                results = node.xpath("{}/text()".format(name))
                if results:
                    sitemap_info[name] = results[0]
            yield sitemap_info


class VirtualSitemapIndex(SitemapIndex):
    """A virtual sitemap index - one that is not actually provided by the
    site, but we build ourselves, containing a list of discovered sitemaps.

    The purpose of this is to use the same interface everywhere, even if we're
    just dealing with a single sitemap.
    """

    def __init__(self, site, sitemaps, url=None):
        self.site = site
        self._sitemaps = sitemaps
        self.url = url

    @property
    def sitemap_infos(self):
        raise NotImplementedError


class SitemapFetcher(object):
    """Looks for a sitemap on a given site, then downloads it and returns a
    ``Sitemap`` object.
    """
    def __init__(self, site):
        self.site = site

    def fetch(self, url=None):
        """Discovers and downloads the sitemap for the given site, returning
        a ``Sitemap`` object.
        """
        if url is not None:
            # We're given an URL to a sitemap, don't do any discovery
            log.info(u'Fetching sitemap {}'.format(url))
            response = requests.get(url)
            sitemap_xml = response.content
            if is_gzipped(response):
                sitemap_xml = gunzip(sitemap_xml)
            return Sitemap(self.site, sitemap_xml, url)

        # No URL given, look for sitemap in common locations
        log.info(u'Fetching sitemap for {}'.format(self.site.url))
        for sm_name in SITEMAP_NAMES:
            url = urljoin(self.site.url, sm_name)
            response = requests.get(url)

            if response.status_code == 200:
                sitemap_xml = response.content

                if is_gzipped(response):
                    sitemap_xml = gunzip(sitemap_xml)

                sitemap = Sitemap(self.site, sitemap_xml, url)
                if sitemap.is_sitemap():
                    return sitemap

        raise NoSitemapFound(
            "No sitemap found for {}!".format(self.site.url))


class Sitemap(object):
    """Represents a single sitemap on a site.
    """

    def __init__(self, site, sitemap_xml, url=None):
        self.site = site
        self.url = url
        self.tree = self._parse_sitemap_xml(sitemap_xml)
        self._url_infos = None

    def is_sitemap(self):
        return len(self.tree.xpath('//urlset')) > 0

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
