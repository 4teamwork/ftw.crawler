import datetime
import json


def isodatetime(dt):
    """Helper function to create a valid, time zone aware ISO 8601 datetime
    in UTC (Zulu time).
    """
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
    return dt.strftime(fmt)


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
            return isodatetime(obj)
        else:
            return super(ExtendedJSONEncoder, self).default(obj)
