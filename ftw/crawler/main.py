from ftw.crawler.config import get_config
from ftw.crawler.gatherer import URLGatherer


def main():
    config = get_config()
    for site_url in config['sites']:
        gatherer = URLGatherer(site_url)
        sitemap = gatherer.fetch_sitemap()
        print "Sitemap for {}:".format(site_url)
        print sitemap


if __name__ == '__main__':
    main()
