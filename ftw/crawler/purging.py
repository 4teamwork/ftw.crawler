from ftw.crawler.solr import SolrConnector
import logging


log = logging.getLogger(__name__)


def purge_removed_docs_from_index(config, sitemap_index, indexed_docs):
    solr = SolrConnector(config.solr)
    unique_field = config.unique_field
    url_field = config.url_field
    site = sitemap_index.site

    log.info(u'Purging removed docs from index for {}...'.format(site.url))
    docs_to_purge = []

    for doc in indexed_docs:
        url = doc[url_field]
        uid = doc[unique_field]

        url_in_site = url.startswith(site.url)
        url_in_any_sitemap = any(url in sm for sm in sitemap_index.sitemaps)

        if url_in_site and not url_in_any_sitemap:
            docs_to_purge.append((uid, url))

    for uid, url in docs_to_purge:
        log.info(u'Purging document {} ({}) from Solr'.format(uid, url))
        solr.delete(uid)
    log.info(u'Done purging.')
