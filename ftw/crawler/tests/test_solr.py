from ftw.crawler.exceptions import SolrError
from ftw.crawler.solr import solr_escape
from ftw.crawler.solr import SolrConnector
from ftw.crawler.testing import CrawlerTestCase
from ftw.crawler.testing import SolrTestCase
from ftw.crawler.tests.helpers import MockResponse
from mock import patch
import json


class TestSolrConnector(SolrTestCase):

    def setUp(self):
        SolrTestCase.setUp(self)
        self.response_ok = self.create_solr_response()

        docs = [{'Title': 'Foobar'}, {'Title': 'Foo bar'}]
        self.response_search_results = self.create_solr_results(docs)

        self.response_400_bad_request = self.create_solr_response(
            status=400,
            content='{"responseHeader":{"status":400,"QTime":0},'
                    '"error":''{"msg":"Something went wrong","code":400}}')

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

    @patch('requests.get')
    def test_search_returns_documents(self, request):
        request.return_value = self.response_search_results
        solr = SolrConnector('http://localhost:8983/solr')

        docs = solr.search('Title:Foo*')
        self.assertEquals([{'Title': 'Foobar'}, {'Title': 'Foo bar'}], docs)

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

    @patch('requests.get')
    def test_search_sends_proper_request_to_solr(self, request):
        request.return_value = self.response_search_results
        solr = SolrConnector('http://localhost:8983/solr')

        query = 'Title:Foo*'
        expected_url = 'http://localhost:8983/solr/select'
        expected_headers = {'Content-Type': 'application/json'}
        params = {'q': query, 'wt': 'json'}

        solr.search(query)

        request.assert_called_with(
            expected_url, headers=expected_headers, params=params)

    @patch('ftw.crawler.solr.log')
    @patch('requests.post')
    def test_index_logs_non_200_responses_from_solr(self, request, log):
        request.return_value = self.response_400_bad_request

        solr = SolrConnector('http://localhost:8983/solr')
        solr.index({'field': 'value'})
        self.assertTrue(log.error.called)

    @patch('ftw.crawler.solr.log')
    @patch('requests.post')
    def test_delete_logs_non_200_responses_from_solr(self, request, log):
        request.return_value = self.response_400_bad_request

        solr = SolrConnector('http://localhost:8983/solr')
        solr.delete('12345')
        self.assertTrue(log.error.called)

    @patch('ftw.crawler.solr.log')
    @patch('requests.get')
    def test_search_raises_on_non_200_responses_from_solr(self, request, log):
        request.return_value = self.response_400_bad_request
        solr = SolrConnector('http://localhost:8983/solr')

        with self.assertRaises(SolrError):
            solr.search('Title:Foo')
            self.assertTrue(log.error.called)

    @patch('requests.get')
    def test_search_honors_fl_argument(self, request):
        request.return_value = self.response_search_results
        solr = SolrConnector('http://localhost:8983/solr')

        solr.search('Title:Foo', fl=('Title', 'UID'))
        args, kwargs = request.call_args
        self.assertIn(('fl', 'Title,UID'), kwargs['params'].items())


class TestSolrEscape(CrawlerTestCase):

    def test_escapes_special_characters(self):
        value = r'+ - && || ! ( ) { } [ ] ^ " ~ * ? : \ /'
        expected = r'\+ \- \&& \|| \! \( \) \{ \} \[ \] '\
                   r'\^ \" \~ \* \? \: \\ \/'

        self.assertEquals(expected, solr_escape(value))
