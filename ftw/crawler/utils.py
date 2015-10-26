from urlparse import urlsplit
from wsgiref.handlers import format_date_time
import calendar
import datetime
import dateutil.parser
import errno
import gzip
import io
import json
import os
import pytz


def to_utc(dt):
    """Ensure that a datetime object is time zone aware and in UTC.
    """
    if dt.tzinfo is None:
        # Naive datetime, assume UTC
        utc_date = pytz.utc.localize(dt)
    else:
        # TZ aware datetime. Convert to UTC if necessary
        utc_date = dt.astimezone(pytz.utc)
    return utc_date


def to_iso_datetime(dt):
    """Create a valid, time zone aware ISO 8601 date/time string in UTC.
    """
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
    return to_utc(dt).strftime(fmt)


def from_iso_datetime(datestring):
    """Parse an ISO 8601 datetime and create a TZ aware datetime object in UTC.
    """
    dt = dateutil.parser.parse(datestring)
    return to_utc(dt)


def to_http_datetime(dt):
    """Create a valid, time zone aware RFC 2616 HTTP datetime string in GMT.
    """
    dt = to_utc(dt)
    # Use calendar.timegm(), NOT time.mktime(), which assumes *local time*
    timestamp = calendar.timegm(dt.timetuple())
    return format_date_time(timestamp)


def from_http_datetime(datestring):
    """Parse an RFC 2616 HTTP datetime string and create a TZ aware datetime
    object in UTC.
    """
    dt = dateutil.parser.parse(datestring)
    return to_utc(dt)


def get_content_type(header_value):
    """Helps deal with the fact that the HTTP Content-Type header may also
    contain a charset declaration. For example:

    text/html; charset=utf-8

    More often than not, we're only interested in the MIME type though.
    """
    if header_value is not None:
        return header_value.split(';')[0]


def is_gzipped(response):
    """Determine whether a response's content is gzipped.

    This only considers the Content-Type header and the filename, NOT
    HTTP compression indicated by the Content-Encoding header, which is
    handled transparently by the `requests` module.
    """
    content_type = get_content_type(response.headers.get('Content-Type'))
    path = urlsplit(response.request.url).path
    return content_type == 'application/x-gzip' or path.endswith('.gz')


def gunzip(bytestring):
    """Decompress a gzipped bytestring.
    """
    with gzip.GzipFile(mode='rb', fileobj=io.BytesIO(bytestring)) as f:
        return f.read()


class ExtendedJSONEncoder(json.JSONEncoder):
    """JSONEncoder that can also serialize datetime objects.
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return to_iso_datetime(obj)
        else:
            return super(ExtendedJSONEncoder, self).default(obj)


def normalize_whitespace(s):
    """Normalize whitespace in a string by
    - replacing all occurences of CR, LF and TAB with a space
    - replacing multiple spaces with only one
    - removing any leading or trailing whitespace
    """
    s = safe_unicode(s)
    return u' '.join(s.split())


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def safe_unicode(value):
    if isinstance(value, str):
        return value.decode('utf-8')
    return value
