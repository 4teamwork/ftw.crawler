import json
import requests


class SolrConnector(object):

    update_handler = 'update'

    def __init__(self, solr_base):
        self.solr_base = solr_base.rstrip('/')
        self.update_url = '{}/{}?{}'.format(
            self.solr_base, SolrConnector.update_handler, 'commit=true')

    def _update_request(self, data):
        headers = {'Content-Type': 'application/json'}
        document = json.dumps(data)
        response = requests.post(
            self.update_url, data=document, headers=headers)
        return response

    def index(self, document):
        response = self._update_request([document])
        return response

    def delete(self, unique_id):
        del_command = {'delete': {'id': unique_id}}
        response = self._update_request(del_command)
        return response
