from ftw.crawler.solr import SolrConnector
import logging


log = logging.getLogger(__name__)


def purge_removed_docs_from_index(config, sitemap, indexed_docs):
    solr = SolrConnector(config.solr)
    unique_field = config.unique_field
    url_field = config.url_field
    site = sitemap.site

    log.info('Purging removed docs from index for site {}...'.format(site.url))
    docs_to_purge = []

    for doc in indexed_docs:
        url = doc[url_field]
        uid = doc[unique_field]
        if url.startswith(site.url) and url not in sitemap:
            docs_to_purge.append((uid, url))

    for uid, url in docs_to_purge:
        log.info('Purging document {} ({}) from Solr'.format(uid, url))
        solr.delete(uid)
    log.info('Done purging.')
