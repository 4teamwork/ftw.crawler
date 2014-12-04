class ResourceInfo(object):

    def __init__(self, filename=None, content_type=None, site=None,
                 url_info=None, last_indexed=None, headers=None,
                 metadata=None, text=None):
        self.filename = filename
        self.content_type = content_type
        self.site = site
        self.url_info = url_info
        self.last_indexed = last_indexed
        self.headers = headers
        self.metadata = metadata
        self.text = text
