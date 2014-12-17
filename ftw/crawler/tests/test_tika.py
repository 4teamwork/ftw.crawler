from ftw.crawler.resource import ResourceInfo
from ftw.crawler.testing import CrawlerTestCase
from ftw.crawler.tests.helpers import MockResponse
from ftw.crawler.tika import TikaConverter
from mock import mock_open
from mock import patch
import csv
import io


# TODO: Figure out how to mock open() without using module globals
open_mock = mock_open()


class TestTikaConverter(CrawlerTestCase):

    def _to_csv(self, mapping):
        csv_buffer = io.BytesIO()
        csv_writer = csv.writer(csv_buffer, delimiter=',', quotechar='"')
        for key, value in mapping.items():
            csv_writer.writerow((key, value))
        return csv_buffer.getvalue()

    @patch('requests.put')
    @patch('ftw.crawler.tika.open', open_mock, create=True)
    def test_extracts_metadata(self, request):
        resource_info = ResourceInfo(content_type='application/pdf')
        metadata = {'title': 'Some title',
                    'creator': 'John Doe'}
        request.return_value = MockResponse(content=self._to_csv(metadata))

        tika = TikaConverter('http://localhost:9998')
        extracted_metadata = tika.extract_metadata(resource_info)

        self.assertEquals(metadata, extracted_metadata)

        for value in extracted_metadata.values():
            if isinstance(value, basestring):
                self.assertIsInstance(value, unicode)

        request.assert_called_with(
            'http://localhost:9998/meta',
            headers={'Content-type': 'application/pdf'},
            data=open_mock.return_value)

    @patch('requests.put')
    @patch('ftw.crawler.tika.open', open_mock, create=True)
    def test_extracts_text(self, request):
        resource_info = ResourceInfo(content_type='application/pdf')
        request.return_value = MockResponse(content='foo bar')

        tika = TikaConverter('http://localhost:9998')
        extracted_text = tika.extract_text(resource_info)

        self.assertEquals(u'foo bar', extracted_text)
        self.assertIsInstance(extracted_text, unicode)
        request.assert_called_with(
            'http://localhost:9998/tika',
            headers={'Content-type': 'application/pdf',
                     'Accept': 'text/plain'},
            data=open_mock.return_value)
