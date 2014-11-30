from ftw.crawler.xml_utils import remove_namespaces
from lxml import etree
import io


SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
PROPERTIES = ('loc', 'lastmod', 'changefreq', 'priority')


class SitemapParser(object):

    def __init__(self, xml_data, site=None):
        self.xml_data = xml_data
        self.site = site
        self._url_infos = None
        self.parse()

    def parse(self):
        tree = etree.parse(io.BytesIO(self.xml_data))
        self.tree = remove_namespaces(tree)

    @property
    def url_infos(self):
        if self._url_infos is None:
            self._url_infos = list(self._get_url_infos())
        return self._url_infos

    def _get_url_infos(self):
        url_nodes = self.tree.xpath('/urlset/url')
        for node in url_nodes:
            url_info = {}
            for name in PROPERTIES:
                results = node.xpath("{}/text()".format(name))
                if results:
                    url_info[name] = results[0]
            yield url_info

    def __contains__(self, url):
        """Tests whether an URL is listed in this sitemap (case-insensitive).
        """
        url_infos = self.url_infos
        return url.lower() in (ui['loc'].lower() for ui in url_infos)
