from ftw.crawler.config import get_config
from ftw.crawler.fetcher import ResourceFetcher
from ftw.crawler.gatherer import URLGatherer
from ftw.crawler.sitemap import SitemapParser
import logging
import shutil
import tempfile


log = logging.getLogger(__name__)


def mktmp(tempdir):
    return tempfile.NamedTemporaryFile(dir=tempdir, delete=False)


def crawl_and_index(tempdir):
    config = get_config()
    for site_url in config['sites']:
        gatherer = URLGatherer(site_url)
        sitemap_xml = gatherer.fetch_sitemap()
        sitemap = SitemapParser(sitemap_xml)
        url_infos = sitemap.get_urls()

        log.info("URLs for {}:".format(site_url))
        for url_info in url_infos:
            log.info("{} {}".format(url_info['loc'], str(url_info)))

            with mktmp(tempdir) as resource_file:
                fetcher = ResourceFetcher(url_info, resource_file)
                resource_fn, content_type = fetcher.fetch()
            log.info("Resource saved to {}".format(resource_fn))

            print
        print


def main():
    tempdir = tempfile.mkdtemp(prefix='ftw.crawler_')
    log.debug("Using temporary directory {}".format(tempdir))
    try:
        crawl_and_index(tempdir)
    finally:
        shutil.rmtree(tempdir)


if __name__ == '__main__':
    main()
