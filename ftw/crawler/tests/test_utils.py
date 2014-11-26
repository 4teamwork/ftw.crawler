from datetime import datetime
from ftw.crawler.utils import ExtendedJSONEncoder
from ftw.crawler.utils import get_content_type
from ftw.crawler.utils import isodatetime
from unittest2 import TestCase


class TestGetContentType(TestCase):

    def test_strips_charset(self):
        header_value = 'text/html; charset=utf-8'
        self.assertEquals('text/html', get_content_type(header_value))

    def test_also_works_for_mimetype_only(self):
        header_value = 'text/html'
        self.assertEquals('text/html', get_content_type(header_value))


class TestISODateTime(TestCase):

    def test_serializes_datetime_to_tz_aware_iso_8601(self):
        dt = datetime(2014, 12, 31, 15, 45, 30, 999)
        self.assertEquals('2014-12-31T15:45:30.000999Z',
                          isodatetime(dt))


class TestExtendedJSONEncoder(TestCase):

    def test_serializes_datetime(self):
        encoder = ExtendedJSONEncoder()
        dt = datetime(2014, 12, 31, 15, 45, 30, 999)
        self.assertEquals('["2014-12-31T15:45:30.000999Z"]',
                          encoder.encode([dt]))

    def test_delegates_unknown_objects_to_default_encoder(self):
        encoder = ExtendedJSONEncoder()
        data = [object()]
        with self.assertRaises(TypeError):
            encoder.encode(data)
