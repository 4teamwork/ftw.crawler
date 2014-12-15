from ftw.crawler import parse_args
from ftw.crawler.configuration import get_config
from ftw.crawler.exceptions import AttemptedRedirect
from ftw.crawler.exceptions import NotModified
from ftw.crawler.extractors import ExtractionEngine
from ftw.crawler.fetcher import ResourceFetcher
from ftw.crawler.gatherer import URLGatherer
from ftw.crawler.purging import purge_removed_docs_from_index
from ftw.crawler.resource import ResourceInfo
from ftw.crawler.sitemap import SitemapParser
from ftw.crawler.solr import solr_escape
from ftw.crawler.solr import SolrConnector
from ftw.crawler.tika import TikaConverter
from ftw.crawler.utils import from_iso_datetime
import logging
import os
import requests
import shutil
import tempfile
from ftw.crawler.exceptions import FetchingError


log = logging.getLogger(__name__)


def display_fields(field_values):
    log.debug("")
    log.debug("=== EXTRACTED FIELD VALUES ===")
    for key, value in field_values.items():
        if key in ('SearchableText', 'snippetText'):
            value = repr(value.strip()[:60]) + '...'
        log.debug("{:<22} {}".format(key + ':', value))
    log.debug("")


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


def get_indexing_time(url, indexed_docs, config):
    for doc in indexed_docs:
        if doc[config.url_field] == url:
            isodate = doc[config.last_modified_field]
            return from_iso_datetime(isodate)
    return None


def crawl_and_index(tempdir, config, options):
    solr = SolrConnector(config.solr)

    for site in config.sites:
        # Skip non-matching sites if we're only indexing a specific URL
        if options.url and not options.url.startswith(site.url):
            continue

        # Fetch and parse the sitemap
        sitemap = get_sitemap(site)

        # Get all docs indexed in Solr for a particular site
        indexed_docs = get_indexed_docs(config, solr, sitemap.site)

        # Purge docs that have been removed from sitemap from Solr index
        purge_removed_docs_from_index(config, sitemap, indexed_docs)

        # Create a requests session to allow for connection pooling
        fetcher_session = requests.Session()

        total = len(sitemap.url_infos)
        log.debug("Crawling {}...".format(sitemap.site.url))

        for n, url_info in enumerate(sitemap.url_infos, start=1):
            url = url_info['loc']
            progress = '[{}/{}]'.format(n, total)

            # If we're only indexing a specific URL, skip all others
            if options.url and not url == options.url:
                continue

            log.debug("{}: {}".format(url, str(url_info)))

            # Get time this document was last indexed
            last_indexed = get_indexing_time(url, indexed_docs, config)

            # Fetch and save resource
            resource_info = ResourceInfo(site=sitemap.site,
                                         url_info=url_info,
                                         last_indexed=last_indexed)
            fetcher = ResourceFetcher(
                resource_info, fetcher_session, tempdir, options)
            try:
                resource_info = fetcher.fetch()
            except NotModified:
                log.info("{}   Skipped {} (not modified)".format(progress, url))
                continue
            except AttemptedRedirect:
                continue
            except FetchingError, e:
                log.error(str(e))
                continue

            # Extract metadata and plain text
            engine = ExtractionEngine(
                config, resource_info, converter=TikaConverter(config.tika))
            field_values = engine.extract_field_values()
            display_fields(field_values)
            os.unlink(resource_info.filename)

            # Index into Solr
            log.debug("Indexing {} into solr.".format(url))
            response = solr.index(field_values)
            if response.status_code == 200:
                log.info("{} * Indexed {}".format(progress, url))

            log.debug("-" * 78)
        log.info("=" * 78)


def main():
    options = parse_args()
    config = get_config(options)

    tempdir = tempfile.mkdtemp(prefix='ftw.crawler_')
    log.debug("Using temporary directory {}".format(tempdir))
    try:
        crawl_and_index(tempdir, config, options)
    finally:
        shutil.rmtree(tempdir)


if __name__ == '__main__':
    main()
