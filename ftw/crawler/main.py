from ftw.crawler.config import get_config
from ftw.crawler.gatherer import URLGatherer
from ftw.crawler.sitemap import SitemapParser


def main():
    config = get_config()
    for site_url in config['sites']:
        gatherer = URLGatherer(site_url)
        sitemap_xml = gatherer.fetch_sitemap()
        sitemap = SitemapParser(sitemap_xml)
        url_infos = sitemap.get_urls()

        print "URLs for {0}:".format(site_url)
        for url_info in url_infos:
            print "{0} {1}".format(url_info['loc'], str(url_info))
        print


if __name__ == '__main__':
    main()
