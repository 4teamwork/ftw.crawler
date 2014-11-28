from datetime import datetime
from ftw.crawler.utils import ExtendedJSONEncoder
from ftw.crawler.utils import from_iso_datetime
from ftw.crawler.utils import get_content_type
from ftw.crawler.utils import to_iso_datetime
from ftw.crawler.utils import to_utc
from pytz import timezone
from unittest2 import TestCase
import pytz


class TestGetContentType(TestCase):

    def test_strips_charset(self):
        header_value = 'text/html; charset=utf-8'
        self.assertEquals('text/html', get_content_type(header_value))

    def test_also_works_for_mimetype_only(self):
        header_value = 'text/html'
        self.assertEquals('text/html', get_content_type(header_value))


class TestToUTC(TestCase):

    def test_doesnt_change_dt_already_in_utc(self):
        dt = datetime(2014, 12, 31, 15, 45, 30, tzinfo=pytz.utc)
        self.assertEquals(dt, to_utc(dt))

    def test_assigns_utc_to_naive_dt(self):
        naive_dt = datetime(2014, 12, 31, 15, 45, 30)
        self.assertEquals(datetime(2014, 12, 31, 15, 45, 30, tzinfo=pytz.utc),
                          to_utc(naive_dt))

    def test_converts_tz_aware_dt_to_utc(self):
        cet = timezone('CET')
        dt = datetime(2014, 12, 31, 16, 45, 30, tzinfo=cet)
        self.assertEquals(datetime(2014, 12, 31, 15, 45, 30, tzinfo=pytz.utc),
                          to_utc(dt))


class TestToISODateTime(TestCase):

    def test_serializes_naive_datetime_to_utc_iso_8601(self):
        dt = datetime(2014, 12, 31, 15, 45, 30, 999)
        self.assertEquals('2014-12-31T15:45:30.000999Z',
                          to_iso_datetime(dt))

    def test_serializes_tz_aware_datetime_to_utc_iso_8601(self):
        cet = timezone('CET')
        dt = datetime(2014, 12, 31, 15, 45, 30, 999, tzinfo=cet)
        self.assertEquals('2014-12-31T14:45:30.000999Z',
                          to_iso_datetime(dt))


class TestFromISODateTime(TestCase):

    def test_parses_utc_iso_8601_to_utc_datetime(self):
        dt = to_utc(datetime(2014, 12, 31, 15, 45, 30))
        self.assertEquals(dt, from_iso_datetime('2014-12-31T15:45:30Z'))
        self.assertEquals(dt, from_iso_datetime('2014-12-31T15:45:30'))
        self.assertEquals(dt, from_iso_datetime('2014-12-31T15:45:30+00:00'))
        self.assertEquals(dt, from_iso_datetime('2014-12-31T16:45:30+01:00'))

    def test_serializes_tz_aware_datetime_to_utc_iso_8601(self):
        cet = timezone('CET')
        dt = datetime(2014, 12, 31, 15, 45, 30, 999, tzinfo=cet)
        self.assertEquals('2014-12-31T14:45:30.000999Z', to_iso_datetime(dt))


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
