from ftw.crawler.exceptions import SolrError
from ftw.crawler.utils import ExtendedJSONEncoder
import logging
import requests


log = logging.getLogger(__name__)


# Solr/lucene reserved characters/terms:
# + - && || ! ( ) { } [ ] ^ " ~ * ? : \ /
SPECIAL_TOKENS = ['+', '-', '&&', '||', '!', '(', ')', '{', '}', '[', ']',
                  '^', '"', '~', '*', '?', ':', '\\', '/']


def solr_escape(value):
    """Escape a value for use in a Solr/Lucene query
    """
    # Deal with backslashes first
    value = value.replace('\\', '\\\\')
    for token in SPECIAL_TOKENS:
        if not token == '\\':
            value = value.replace(token, '\\' + token)
    return value


class SolrConnector(object):

    update_handler = 'update'
    search_handler = 'select'

    def __init__(self, solr_base):
        self.solr_base = solr_base.rstrip('/')

        self.update_url = '{}/{}?{}'.format(
            self.solr_base, SolrConnector.update_handler, 'commit=true')

        self.search_url = '{}/{}'.format(
            self.solr_base, SolrConnector.search_handler)

    def _update_request(self, data):
        headers = {'Content-Type': 'application/json'}
        document = ExtendedJSONEncoder().encode(data)
        response = requests.post(
            self.update_url, data=document, headers=headers)

        if not response.status_code == 200:
            log.error(u"Error from Solr: Status: {}. Response:\n{}".format(
                response.status_code, response.text))
        return response

    def _search_request(self, query, fl=None):
        headers = {'Content-Type': 'application/json'}

        params = {'q': query, 'wt': 'json'}

        if fl is not None:
            params.update({'fl': ','.join(fl)})

        response = requests.get(
            self.search_url, params=params, headers=headers)

        if not response.status_code == 200:
            log.error(u"Error from Solr: Status: {}. Response:\n{}".format(
                response.status_code, response.text))
            raise SolrError(
                "Got status {} from Solr.".format(response.status_code))
        return response

    def index(self, document):
        response = self._update_request([document])
        return response

    def delete(self, unique_id):
        del_command = {'delete': {'id': unique_id}}
        response = self._update_request(del_command)
        return response

    def search(self, query, fl=None):
        response = self._search_request(query, fl)
        search_results = response.json()['response']
        docs = search_results['docs']
        return docs
