def get_content_type(header_value):
    """Helps deal with the fact that the HTTP Content-Type header may also
    contain a charset declaration. For example:

    text/html; charset=utf-8

    More often than not, we're only interested in the MIME type though.
    """
    if header_value is not None:
        return header_value.split(';')[0]
