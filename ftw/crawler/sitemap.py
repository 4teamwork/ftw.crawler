from ftw.crawler.xml_utils import remove_namespaces
from lxml import etree
import io


SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
PROPERTIES = ('loc', 'lastmod', 'changefreq', 'priority')


class SitemapParser(object):

    def __init__(self, xml_data):
        self.xml_data = xml_data
        self.parse()

    def parse(self):
        tree = etree.parse(io.BytesIO(self.xml_data))
        self.tree = remove_namespaces(tree)

    def get_urls(self):
        url_nodes = self.tree.xpath('/urlset/url')
        for node in url_nodes:
            url_info = {}
            for name in PROPERTIES:
                results = node.xpath("{}/text()".format(name))
                if results:
                    url_info[name] = results[0]
            yield url_info
