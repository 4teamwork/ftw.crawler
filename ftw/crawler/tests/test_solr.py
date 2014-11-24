from ftw.crawler.solr import SolrConnector
from ftw.crawler.tests.helpers import MockResponse
from mock import patch
from unittest2 import TestCase
import json


class TestSolrConnector(TestCase):

    def setUp(self):
        self.response_ok = MockResponse(
            content='{"responseHeader":{"status":0,"QTime":10}}',
            headers={'content-type': 'application/json; charset=UTF-8'})

    @patch('requests.post')
    def test_index_returns_response(self, request):
        request.return_value = self.response_ok

        solr = SolrConnector('http://localhost:8983/solr')
        response = solr.index({'field': 'value'})
        self.assertIsInstance(response, MockResponse)

    @patch('requests.post')
    def test_delete_returns_response(self, request):
        request.return_value = self.response_ok

        solr = SolrConnector('http://localhost:8983/solr')
        response = solr.delete('12345')
        self.assertIsInstance(response, MockResponse)

    @patch('requests.post')
    def test_index_sends_proper_request_to_solr(self, request):
        request.return_value = self.response_ok
        solr = SolrConnector('http://localhost:8983/solr')

        expected_url = 'http://localhost:8983/solr/update?commit=true'
        expected_headers = {'Content-Type': 'application/json'}
        data = {'field': 'value'}

        solr.index(data)
        request.assert_called_with(
            expected_url, headers=expected_headers, data=json.dumps([data]))

    @patch('requests.post')
    def test_delete_sends_proper_request_to_solr(self, request):
        request.return_value = self.response_ok
        solr = SolrConnector('http://localhost:8983/solr')

        expected_url = 'http://localhost:8983/solr/update?commit=true'
        expected_headers = {'Content-Type': 'application/json'}
        uid = '12345'
        cmd = {'delete': {'id': uid}}

        solr.delete(uid)
        request.assert_called_with(
            expected_url, headers=expected_headers, data=json.dumps(cmd))
