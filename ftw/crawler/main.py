from ftw.crawler import parse_args
from ftw.crawler.configuration import get_config
from ftw.crawler.extractors import ExtractionEngine
from ftw.crawler.fetcher import ResourceFetcher
from ftw.crawler.gatherer import URLGatherer
from ftw.crawler.resource import ResourceInfo
from ftw.crawler.sitemap import SitemapParser
from ftw.crawler.solr import SolrConnector
from ftw.crawler.tika import TikaConverter
import logging
import os
import shutil
import tempfile


log = logging.getLogger(__name__)


def print_fields(field_values):
    print
    print "=== FIELD VALUES ===="
    for key, value in field_values.items():
        if key in ('SearchableText', 'snippetText'):
            value = repr(value.strip()[:60]) + '...'
        print "{:<22} {}".format(key + ':', value)
    print


def crawl_and_index(tempdir, config):
    solr = SolrConnector(config.solr)

    for site in config.sites:
        gatherer = URLGatherer(site.url)

        # Fetch sitemap
        sitemap_xml = gatherer.fetch_sitemap()
        sitemap = SitemapParser(sitemap_xml)
        url_infos = sitemap.get_urls()

        log.info("URLs for {}:".format(site.url))
        for url_info in url_infos:
            log.info("{} {}".format(url_info['loc'], str(url_info)))

            # Fetch and save resource
            resource_info = ResourceInfo(site=site, url_info=url_info)
            fetcher = ResourceFetcher(resource_info, tempdir)
            resource_info = fetcher.fetch()
            log.info("Resource saved to {}".format(resource_info.filename))

            # Extract metadata and plain text
            engine = ExtractionEngine(
                config, resource_info, converter=TikaConverter(config.tika))
            field_values = engine.extract_field_values()
            print_fields(field_values)
            os.unlink(resource_info.filename)

            # Index into Solr
            log.info("Indexing {} into solr.".format(url_info['loc']))
            solr.index(field_values)

            print
        print


def main():
    args = parse_args()
    config = get_config(args)

    tempdir = tempfile.mkdtemp(prefix='ftw.crawler_')
    log.debug("Using temporary directory {}".format(tempdir))
    try:
        crawl_and_index(tempdir, config)
    finally:
        shutil.rmtree(tempdir)


if __name__ == '__main__':
    main()
