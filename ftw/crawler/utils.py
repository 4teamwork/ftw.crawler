import datetime
import dateutil.parser
import json
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


def get_content_type(header_value):
    """Helps deal with the fact that the HTTP Content-Type header may also
    contain a charset declaration. For example:

    text/html; charset=utf-8

    More often than not, we're only interested in the MIME type though.
    """
    if header_value is not None:
        return header_value.split(';')[0]


class ExtendedJSONEncoder(json.JSONEncoder):
    """JSONEncoder that can also serialize datetime objects.
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return to_iso_datetime(obj)
        else:
            return super(ExtendedJSONEncoder, self).default(obj)
