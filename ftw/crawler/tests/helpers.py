from pkg_resources import resource_string


def get_asset(filename):
    return resource_string('ftw.crawler.tests.assets', filename)


class MockFile(object):

    def __init__(self, name=None):
        self.name = name
        self._buf = ''

    def close(self):
        pass

    def write(self, data):
        self._buf += data
        return len(data)

    def seek(self, pos):
        pass

    def read(self):
        return self._buf


class MockRequest(object):

    def __init__(self, url='http://example.org'):
        self.url = url


class MockResponse(object):

    def __init__(self, content=None, status_code=200, headers=None,
                 request=None):
        self.content = content
        self.status_code = status_code

        if headers is None:
            headers = {}
        self.headers = headers

        if request is None:
            request = MockRequest()
        self.request = request


class MockConverter(object):

    def __init__(self, metadata=None, text=''):
        if metadata is None:
            metadata = {}
        self.metadata = metadata

        self.text = text

    def extract_metadata(self, fileobj, content_type, filename):
        return self.metadata

    def extract_text(self, fileobj, content_type, filename):
        return self.text
