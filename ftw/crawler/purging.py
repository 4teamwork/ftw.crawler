from ftw.crawler.solr import solr_escape
import logging


log = logging.getLogger(__name__)


def purge_removed_docs_from_index(config, solr, sitemaps):
    unique_field = config.unique_field
    url_field = config.url_field

    log.info('Purging removed docs from index...')
    for sitemap in sitemaps:
        docs_to_purge = []
        site = sitemap.site
        query = '{}:{}*'.format(url_field, solr_escape(site.url))
        indexed_docs = solr.search(query)
        for doc in indexed_docs:
            url = doc[url_field]
            uid = doc[unique_field]
            if url.startswith(site.url) and url not in sitemap:
                docs_to_purge.append((uid, url))

        for uid, url in docs_to_purge:
            log.info('Purging document {} ({}) from Solr'.format(uid, url))
            solr.delete(uid)
    log.info('Done purging.')
