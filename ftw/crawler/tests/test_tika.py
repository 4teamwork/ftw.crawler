from ftw.crawler.tests.helpers import MockResponse
from ftw.crawler.tika import TikaConverter
from mock import patch
from unittest2 import TestCase
import csv
import io


class TestTikaConverter(TestCase):

    def _to_csv(self, mapping):
        csv_buffer = io.BytesIO()
        csv_writer = csv.writer(csv_buffer, delimiter=',', quotechar='"')
        for key, value in mapping.items():
            csv_writer.writerow((key, value))
        return csv_buffer.getvalue()

    @patch('requests.put')
    def test_extracts_metadata(self, request):
        fileobj = io.BytesIO('')
        metadata = {'title': 'Some title',
                    'creator': 'John Doe'}
        request.return_value = MockResponse(content=self._to_csv(metadata))

        tika = TikaConverter('http://localhost:9998')
        extracted_metadata = tika.extract_metadata(
            fileobj, 'application/pdf', 'foo.pdf')

        self.assertEquals(metadata, extracted_metadata)
        request.assert_called_with(
            'http://localhost:9998/meta',
            headers={'Content-type': 'application/pdf'},
            data=fileobj)
