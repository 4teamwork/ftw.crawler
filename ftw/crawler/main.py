from ftw.crawler import parse_args
from ftw.crawler.configuration import get_config
from ftw.crawler.exceptions import AttemptedRedirect
from ftw.crawler.extractors import ExtractionEngine
from ftw.crawler.fetcher import ResourceFetcher
from ftw.crawler.gatherer import URLGatherer
from ftw.crawler.purging import purge_removed_docs_from_index
from ftw.crawler.resource import ResourceInfo
from ftw.crawler.sitemap import SitemapParser
from ftw.crawler.solr import solr_escape
from ftw.crawler.solr import SolrConnector
from ftw.crawler.tika import TikaConverter
import logging
import os
import requests
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


def get_sitemap(site):
    gatherer = URLGatherer(site.url)
    sitemap_xml = gatherer.fetch_sitemap()
    sitemap = SitemapParser(sitemap_xml, site=site)
    return sitemap


def get_indexed_docs(config, solr, site):
    query = '{}:{}*'.format(config.url_field, solr_escape(site.url))
    indexed_docs = solr.search(
        query,
        fl=(config.unique_field, config.url_field, config.last_modified_field))
    return indexed_docs


def crawl_and_index(tempdir, config):
    solr = SolrConnector(config.solr)

    for site in config.sites:
        # Fetch and parse the sitemap
        sitemap = get_sitemap(site)

        # Get all docs indexed in Solr for a particular site
        indexed_docs = get_indexed_docs(config, solr, sitemap.site)

        # Purge docs that have been removed from sitemap from Solr index
        purge_removed_docs_from_index(config, sitemap, indexed_docs)

        # Create a requests session to allow for connection pooling
        fetcher_session = requests.Session()

        log.info("URLs for {}:".format(sitemap.site.url))
        for url_info in sitemap.url_infos:
            log.info("{} {}".format(url_info['loc'], str(url_info)))

            # Fetch and save resource
            resource_info = ResourceInfo(site=sitemap.site, url_info=url_info)
            fetcher = ResourceFetcher(resource_info, fetcher_session, tempdir)

            try:
                resource_info = fetcher.fetch()
            except AttemptedRedirect:
                continue

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
