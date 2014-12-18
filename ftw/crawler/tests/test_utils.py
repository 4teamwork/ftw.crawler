from datetime import datetime
from ftw.crawler.testing import CrawlerTestCase
from ftw.crawler.utils import ExtendedJSONEncoder
from ftw.crawler.utils import from_http_datetime
from ftw.crawler.utils import from_iso_datetime
from ftw.crawler.utils import get_content_type
from ftw.crawler.utils import normalize_whitespace
from ftw.crawler.utils import to_http_datetime
from ftw.crawler.utils import to_iso_datetime
from ftw.crawler.utils import to_utc
from pytz import timezone
import pytz


class TestGetContentType(CrawlerTestCase):

    def test_strips_charset(self):
        header_value = 'text/html; charset=utf-8'
        self.assertEquals('text/html', get_content_type(header_value))

    def test_also_works_for_mimetype_only(self):
        header_value = 'text/html'
        self.assertEquals('text/html', get_content_type(header_value))


class TestToUTC(CrawlerTestCase):

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


class TestToISODateTime(CrawlerTestCase):

    def test_serializes_naive_datetime_to_utc_iso_8601(self):
        dt = datetime(2014, 12, 31, 15, 45, 30, 999)
        self.assertEquals('2014-12-31T15:45:30.000999Z',
                          to_iso_datetime(dt))

    def test_serializes_tz_aware_datetime_to_utc_iso_8601(self):
        cet = timezone('CET')
        dt = datetime(2014, 12, 31, 15, 45, 30, 999, tzinfo=cet)
        self.assertEquals('2014-12-31T14:45:30.000999Z',
                          to_iso_datetime(dt))


class TestFromISODateTime(CrawlerTestCase):

    def test_parses_utc_iso_8601_to_utc_datetime(self):
        dt = to_utc(datetime(2014, 12, 31, 15, 45, 30))
        self.assertEquals(dt, from_iso_datetime('2014-12-31T15:45:30Z'))
        self.assertEquals(dt, from_iso_datetime('2014-12-31T15:45:30'))
        self.assertEquals(dt, from_iso_datetime('2014-12-31T15:45:30+00:00'))
        self.assertEquals(dt, from_iso_datetime('2014-12-31T16:45:30+01:00'))


class TestToHTTPDateTime(CrawlerTestCase):

    def test_serializes_naive_datetime_to_rfc_2616_http_date(self):
        dt = datetime(2014, 12, 31, 15, 45, 30, 999)
        self.assertEquals('Wed, 31 Dec 2014 15:45:30 GMT',
                          to_http_datetime(dt))

    def test_serializes_tz_aware_datetime_to_rfc_2616_http_date(self):
        cet = timezone('CET')
        dt = datetime(2014, 12, 31, 15, 45, 30, 999, tzinfo=cet)
        self.assertEquals('Wed, 31 Dec 2014 14:45:30 GMT',
                          to_http_datetime(dt))


class TestFromHTTPDateTime(CrawlerTestCase):

    def test_parses_rfc2616_http_date_to_utc_datetime(self):
        from_http = from_http_datetime
        dt = to_utc(datetime(2014, 6, 30, 15, 45, 30))
        # Test parsing of the three formats described by RFC 2616

        # RFC 1123
        self.assertEquals(dt, from_http('Mon, 30 Jun 2014 15:45:30 GMT'))
        # RFC 850
        self.assertEquals(dt, from_http('Monday, 30-Jun-14 15:45:30 GMT'))
        # ANSI C's asctime() Sun Nov  6 08:49:37 1994
        self.assertEquals(dt, from_http('Mon Jun 30 15:45:30 2014'))

        # Test a date in winter as well to trigger any DST issues
        dt_s = to_utc(datetime(2014, 12, 31, 15, 45, 30))
        self.assertEquals(dt_s, from_http('Wed, 31 Dec 2014 15:45:30 GMT'))


class TestNormalizeWhitespace(CrawlerTestCase):

    def test_replaces_tabs_with_space(self):
        self.assertEquals('x x', normalize_whitespace('x\tx'))

    def test_replaces_cr_with_space(self):
        self.assertEquals('x x', normalize_whitespace('x\rx'))

    def test_replaces_lf_with_space(self):
        self.assertEquals('x x', normalize_whitespace('x\nx'))

    def test_strips_leading_and_trailing_whitespace(self):
        self.assertEquals('x', normalize_whitespace(' \r\n \tx \r\n \t '))

    def test_replaces_multiple_whitespaces_by_one(self):
        self.assertEquals('a b c', normalize_whitespace('a  b     c'))


class TestExtendedJSONEncoder(CrawlerTestCase):

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
