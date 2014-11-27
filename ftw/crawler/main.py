from ftw.crawler import parse_args
from ftw.crawler.configuration import get_config
from ftw.crawler.extractors import ExtractionEngine
from ftw.crawler.fetcher import ResourceFetcher
from ftw.crawler.gatherer import URLGatherer
from ftw.crawler.sitemap import SitemapParser
from ftw.crawler.solr import SolrConnector
from ftw.crawler.tika import TikaConverter
import logging
import os
import shutil
import tempfile


log = logging.getLogger(__name__)


def mktmp(tempdir):
    return tempfile.NamedTemporaryFile(dir=tempdir, delete=False)


def print_fields(field_values):
    print
    print "=== FIELD VALUES ===="
    for key, value in field_values.items():
        if key == 'SearchableText':
            value = repr(value.strip()[:60]) + '...'
        print "{:<17} {}".format(key + ':', value)
    print


def crawl_and_index(tempdir, config):
    solr = SolrConnector(config.solr)

    for site in config.sites:
        gatherer = URLGatherer(site.url)
        sitemap_xml = gatherer.fetch_sitemap()
        sitemap = SitemapParser(sitemap_xml)
        url_infos = sitemap.get_urls()

        log.info("URLs for {}:".format(site.url))
        for url_info in url_infos:
            log.info("{} {}".format(url_info['loc'], str(url_info)))

            with mktmp(tempdir) as resource_file:
                fetcher = ResourceFetcher(url_info, resource_file)
                resource_fn, content_type = fetcher.fetch()
            log.info("Resource saved to {}".format(resource_fn))

            with open(resource_fn) as resource_file:
                engine = ExtractionEngine(
                    config, site, url_info, resource_file,
                    content_type=content_type, filename='',
                    fields=config.fields, converter=TikaConverter(config.tika))
                field_values = engine.extract_field_values()
                print_fields(field_values)
            os.unlink(resource_fn)

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
